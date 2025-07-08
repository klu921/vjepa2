"""
This file contains all functions for IMAGE CAPTIONING.

def __init__(): initializes the VLM model and processor
def caption_image(): [path to image, image prompt -> image caption] Captions a single image according to a list of injectible prompt.
def caption_frames(): [list of frames: [timestamp, path to image, image array] -> list of captions] Captions a list of frames, using caption_image.
def save_captions(): [list of captions -> path to json file] Saves a list of captions to a json file.
"""

from transformers import InstructBlipProcessor, InstructBlipForConditionalGeneration, AutoProcessor, AutoModelForCausalLM, AutoModelForImageTextToText
from PIL import Image
import torch
from typing import List, Dict, Any
import json
import os
from together import Together
import base64
import time

# Set custom cache directory for model weights
#os.makedirs("data/", exist_ok=True)

client = Together()

class ImageCaptioner:
    def __init__(self, model_name: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"):
        """
        Initialize the image captioning model
        """
        self.model_name = model_name
        
        print(f"Model loaded successfully")

    def caption_image(self, image_path: str, prompt: str) -> str:
        """
        Generate detailed caption for a single image by querying meta on together api
        """
        
        max_retries = 6
        retry_delay = 10 
        
        for attempt in range(max_retries):
            try:
                with open(image_path, "rb") as image_file:
                    image = base64.b64encode(image_file.read()).decode('utf-8')

                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {
                                    "url": f"data:image/jpeg;base64,{image}"}},
                            ]}
                    ],
                    stream = False
                )

                generated_text = response.choices[0].message.content    
                return generated_text.strip()
                
            except Exception as e:
                if "rate" in str(e).lower() and attempt < max_retries - 1:
                    print(e)
                    print(f"Rate limited on attempt {attempt + 1}. Waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Error captioning image {image_path}: {e}")
                    return "Error generating caption"
    
   
    
    def caption_batch(self, image_paths: List[str], prompt: str) -> List[str]:
        """
        Caption up to 20 images at once
        """
        max_retries = 6
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                # Create multi-image prompt with sample and detailed formatting instructions
                multi_prompt = f"""{prompt}

CRITICAL: You must provide EXTREME DETAIL for each image following this EXACT format. Here is an example of the level of detail required:

EXAMPLE FORMAT:
Image 1:
Objects:
- The man: He is an older adult with short gray hair and a mustache. He is wearing a yellow T-shirt with red stripes and a red star on the chest. The shirt appears to be made of a lightweight, possibly cotton material. He is standing in a hallway, looking directly at the camera with a neutral expression. His skin tone is fair, and he has a few wrinkles around his eyes and mouth. He is positioned in front of a dark-colored door.
- The mirror: It is a large, round mirror with a black frame. The mirror is mounted on a white wall in a hallway. It reflects the image of the hallway, including another door, a tiled floor, and various objects in the background. The mirror's surface is smooth and reflective.
- The hallway: The hallway has white walls and a tiled floor. There are several doors leading off the hallway, including the one behind the man and another visible in the reflection of the mirror. The hallway is well-lit, with light coming from an unseen source.

Actions:
- The man is standing still, looking directly at the camera. There are no other apparent actions in the image.

Setting/context:
- The image was taken in a residential setting, likely a home or apartment. The hallway and doors suggest a private living space. The presence of various objects in the background, such as furniture and personal items, further supports this interpretation. The image appears to be a casual, informal photograph, possibly taken by the man himself or someone else in the household.

IMPORTANT: Caption each image independently without referring to other images in this batch. Treat each image as completely separate and describe it fully on its own.

NOW CAPTION EACH IMAGE WITH THIS SAME EXTREME LEVEL OF DETAIL:

Image 1:
Objects:
- [Describe EVERY object with extreme detail: exact colors, materials, textures, shapes, sizes, positions, relationships, conditions, etc.]

Actions:
- [Describe ALL actions, movements, gestures, expressions, interactions in complete detail]

Setting/context:
- [Describe the complete environment, lighting, atmosphere, spatial layout, context, purpose, etc.]

Image 2:
Objects:
- [Same extreme detail level - describe independently without referencing Image 1]

Actions:
- [Same extreme detail level - describe independently without referencing Image 1]

Setting/context:
- [Same extreme detail level - describe independently without referencing Image 1]

Continue this pattern for all images. Each image description must be COMPLETELY INDEPENDENT. BE EXTREMELY THOROUGH AND DETAILED."""
                
                content = [{"type": "text", "text": multi_prompt}]
                
                # Add up to 20 images
                for image_path in image_paths:
                    with open(image_path, "rb") as image_file:
                        image = base64.b64encode(image_file.read()).decode('utf-8')
                        content.append({
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/jpeg;base64,{image}"}
                        })

                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": content}],
                    stream=False
                )

                # Parse response to extract individual captions
                response_text = response.choices[0].message.content
                print(response_text)
                captions = []
                
                # Parse detailed multi-image response
                captions = self._parse_detailed_multi_image_response(response_text, len(image_paths))
                
                return captions
                
            except Exception as e:
                if "rate" in str(e).lower() and attempt < max_retries - 1:
                    print(e)
                    print(f"Rate limited on attempt {attempt + 1}. Waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"Error captioning batch: {e}")
                    return ["Error generating caption"] * len(image_paths)
    
    def _parse_detailed_multi_image_response(self, response_text: str, num_images: int) -> List[str]:
        """
        Parse detailed multi-image response with Objects/Actions/Setting format
        """
        captions = []
        
        # Split response by "Image X:" markers
        image_sections = []
        lines = response_text.split('\n')
        current_section = []
        current_image = 0
        
        for line in lines:
            # Check if this line starts a new image section
            if line.strip().startswith('Image ') and ':' in line:
                # Save previous section if it exists
                if current_section and current_image > 0:
                    image_sections.append('\n'.join(current_section))
                # Start new section
                current_section = [line]
                current_image += 1
            else:
                current_section.append(line)
        
        # Add the last section
        if current_section and current_image > 0:
            image_sections.append('\n'.join(current_section))
        
        # Extract captions from each section
        for i in range(num_images):
            if i < len(image_sections):
                section = image_sections[i]
                # Remove the "Image X:" header and get the caption content
                lines = section.split('\n')[1:]  # Skip first line with "Image X:"
                caption = '\n'.join(lines).strip()
                captions.append(caption)
            else:
                captions.append("Caption not found")
        
        return captions

    def caption_frames(self, frame_data: List[tuple], prompt: str) -> List[Dict[str, Any]]:
        """
        frame_data: List of (timestamp, frame_path, frame_array) tuples
        """
        
        captioned_frames = []
        
        # Check if captions file exists and load existing data
        captions_file = "captions/video_captions.json"
        if os.path.exists(captions_file):
            with open(captions_file, "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Determine starting frame (resume from where we left off)
        start_frame = len(existing_data)
        
        if start_frame >= len(frame_data):
            print(f"All {len(frame_data)} frames already captioned")
            return existing_data
        
        print(f"Starting from frame {start_frame + 1}/{len(frame_data)}")
        
        # Process frames in batches of 20
        batch_size = 10
        remaining_frames = frame_data[start_frame:]
        
        for batch_start in range(0, len(remaining_frames), batch_size):
            batch_end = min(batch_start + batch_size, len(remaining_frames))
            batch_frames = remaining_frames[batch_start:batch_end]
            
            batch_paths = [frame[1] for frame in batch_frames]
            
            batch_captions = self.caption_batch(batch_paths, prompt)
            
            for i, (frame, caption) in enumerate(zip(batch_frames, batch_captions)):
                frame_caption = {
                    'timestamp': frame[0],
                    'frame_path': frame[1],
                    'captions': caption
                }
                captioned_frames.append(frame_caption)
                existing_data.append(frame_caption)
                
                # Print the caption
                print(f"Frame {frame[1]} ({frame[0]:.2f}s): {caption}")
            
            # Save progress after each batch
            with open(captions_file, "w") as f:
                json.dump(existing_data, f, indent=2)
            
            print(f"Captioned batch {batch_start//batch_size + 1} ({len(batch_frames)} frames)")
            
        return existing_data
    

if __name__ == "__main__":
    # Test the captioner
    captioner = ImageCaptioner()
    
    # This would be used with actual frame data
    print("Image captioning system initialized successfully")