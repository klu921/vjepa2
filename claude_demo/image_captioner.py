from transformers import InstructBlipProcessor, InstructBlipForConditionalGeneration, AutoProcessor, AutoModelForCausalLM
from PIL import Image
import torch
from typing import List, Dict, Any
import json
import os

# Set custom cache directory for model weights
os.makedirs("data/", exist_ok=True)

CACHE_DIR = "data/instructblip_xl_weights"

processor = InstructBlipProcessor.from_pretrained("Salesforce/instructblip-flan-t5-xl", cache_dir=CACHE_DIR)
model = InstructBlipForConditionalGeneration.from_pretrained("Salesforce/instructblip-flan-t5-xl", cache_dir=CACHE_DIR)

class ImageCaptioner:
    def __init__(self, model_name: str = "Salesforce/instructblip-flan-t5-xl"):
        """
        Initialize the image captioning model
        Using InstructBLIP-XL for detailed, prompted image captioning with multi-GPU support
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = InstructBlipProcessor.from_pretrained(model_name, cache_dir=CACHE_DIR)
        self.model = InstructBlipForConditionalGeneration.from_pretrained(model_name, cache_dir=CACHE_DIR).to(self.device)   

    def caption_image(self, image_path: str, prompt: str = None) -> str:
        """
        Generate detailed caption for a single image using InstructBLIP-XL
        """
        prompts = [
            "Describe the central objects in this image, how they are positioned, interact with each other, and how they relate to the background.Also, describe the setting, environment, and background of this image in great depth.",
            "What are the people doing in this image? Describe their actions and interactions. Describe any text, signs, or written content visible in this image.",
            "Generate a summary of this image as if you're preparing for a spatial intelligence task, where questions will ask about navigation, location, and orientation.",
        ]
        
        captions = ""

        try:
            image = Image.open(image_path).convert('RGB')
            for prompt in prompts:

                inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device)
                
                with torch.no_grad():
                    generated_ids = self.model.generate(
                        **inputs, 
                        max_new_tokens=150, 
                        do_sample=False,
                        num_beams=3
                    )
            
                caption = self.processor.decode(generated_ids[0], skip_special_tokens=True)
                captions = captions + " " + caption

            return captions
            
        except Exception as e:
            print(f"Error captioning image {image_path}: {e}")
            return "Error generating caption"
    
   
    
    def caption_frames(self, frame_data: List[tuple]) -> List[Dict[str, Any]]:
        """
        frame_data: List of (timestamp, frame_path, frame_array) tuples
        batch_size: Number of images to process in parallel (auto-calculated based on GPU count)
        """
        
        captioned_frames = []
        
        for i in range(0, len(frame_data)):
            img = frame_data[i][1]
            caption = self.caption_image(img)
            captioned_frames.append({
                'timestamp': frame_data[i][0],
                'frame_path': frame_data[i][1],
                'captions': caption
            })
            if i % 1 == 0:
                print(f"Captioned {i} frames")
        
        return captioned_frames
    
    def save_captions(self, captioned_frames: List[Dict], output_path: str = "data/video_captions.json"):
        """
        Save all captions to a JSON file for offline querying
        """
        with open(output_path, 'w') as f:
            json.dump(captioned_frames, f, indent=2)
        
        print(f"Saved {len(captioned_frames)} captioned frames to {output_path}")


if __name__ == "__main__":
    # Test the captioner
    captioner = ImageCaptioner()
    
    # This would be used with actual frame data
    print("Image captioning system initialized successfully")