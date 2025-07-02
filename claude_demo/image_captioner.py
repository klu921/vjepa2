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
        Using InstructBLIP-XL for detailed, prompted image captioning
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        self.processor = InstructBlipProcessor.from_pretrained(model_name, cache_dir=CACHE_DIR)
        self.model = InstructBlipForConditionalGeneration.from_pretrained(model_name, cache_dir=CACHE_DIR)
        self.model.to(self.device)
        
        print(f"Loaded model: {model_name}")
    
    def caption_image(self, image_path: str, prompt: str = None) -> str:
        """
        Generate detailed caption for a single image using InstructBLIP-XL
        """
        try:
            image = Image.open(image_path).convert('RGB')
            
            if prompt:
                # InstructBLIP works well with prompts
                inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device)
            else:
                # Default prompt for general captioning
                inputs = self.processor(images=image, text="Describe this image in detail.", return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs, 
                    max_new_tokens=150, 
                    do_sample=False,
                    num_beams=3
                )
            
            caption = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            return caption
            
        except Exception as e:
            print(f"Error captioning image {image_path}: {e}")
            return "Error generating caption"
    
    def detailed_caption_with_prompts(self, image_path: str) -> Dict[str, str]:
        """
        Generate multiple detailed captions with different prompts for comprehensive understanding
        """

        prompts = [
            "Describe this image in detail, including all objects, people, and activities:",
            "What are the people doing in this image? Describe their actions and interactions:",
            "Describe the setting, environment, and background of this image:",
            "What objects can you see in this image? List them and their locations:",
            "Describe any text, signs, or written content visible in this image:",
            "Generate captions for a spatial intelligence task, where questions will ask about navigation, location, and orientation.",
            "What are the layouts, relationships between objects, proximity of objects to each other and users, and other spatial properties of this image?"
        ]
        
        captions = {}
        
        # General caption without prompt
        captions['general'] = self.caption_image(image_path)
        
        # Specific prompted captions
        for i, prompt in enumerate(prompts):
            key = f"detailed_{i+1}"
            captions[key] = self.caption_image(image_path, prompt)
        
        return captions
    
    def batch_caption_frames(self, frame_data: List[tuple]) -> List[
        Dict[str, Any]]:
        """
        Caption all frames with comprehensive details
        frame_data: List of (timestamp, frame_path, frame_array) tuples
        """
        captioned_frames = []
        
        #TODO: remove this limit, this is just for testing
        for timestamp, frame_path, _ in frame_data[:5]:
            print(f"Captioning frame at {timestamp:.2f}s...")
            
            # Get comprehensive captions
            detailed_captions = self.detailed_caption_with_prompts(frame_path)
            
            frame_info = {
                'timestamp': timestamp,
                'frame_path': frame_path,
                'captions': detailed_captions
            }
            
            captioned_frames.append(frame_info)
        
        return captioned_frames
    
    def save_captions(self, captioned_frames: List[Dict], output_path: str = "data/video_captions.json"):
        """
        Save all captions to a JSON file for offline querying
        """
        with open(output_path, 'w') as f:
            json.dump(captioned_frames, f, indent=2)
        
        print(f"Saved {len(captioned_frames)} captioned frames to {output_path}")

class DetailedCaptioner:
    """
    Alternative captioner using a more detailed model for even better descriptions
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Using a more detailed captioning model
        model_name = "microsoft/git-large-coco"
        git_cache_dir = "/home/klu/LCVR/claude_demo/data/git_weights"
        os.makedirs(git_cache_dir, exist_ok=True)
        self.processor = AutoProcessor.from_pretrained(model_name, cache_dir=git_cache_dir)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=git_cache_dir)
        self.model.to(self.device)
    
    def caption_image(self, image_path: str) -> str:
        image = Image.open(image_path).convert('RGB')
        
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            generated_ids = self.model.generate(
                pixel_values=inputs.pixel_values,
                max_length=200,
                num_beams=4,
                early_stopping=True
            )
        
        caption = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return caption

if __name__ == "__main__":
    # Test the captioner
    captioner = ImageCaptioner()
    
    # This would be used with actual frame data
    print("Image captioning system initialized successfully")