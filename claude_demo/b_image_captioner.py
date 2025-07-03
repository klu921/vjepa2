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

# Set custom cache directory for model weights
os.makedirs("data/", exist_ok=True)

CACHE_DIR = "data/qwen_vl_7b_instruct_weights"

# Global model instantiation removed - moved to class

class ImageCaptioner:
    def __init__(self, model_name: str = "Qwen/Qwen2-VL-7B-Instruct"):
        """
        Initialize the image captioning model
        Using Qwen2-VL-7B on single GPU
        """
        print(f"Loading model {model_name} on single GPU...")
        print(f"Available GPUs: {torch.cuda.device_count()}")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoProcessor.from_pretrained(model_name, cache_dir=CACHE_DIR)
        self.model = AutoModelForImageTextToText.from_pretrained(
            model_name, 
            cache_dir=CACHE_DIR,
            torch_dtype=torch.float16,
            trust_remote_code=True
        ).to(self.device)
        
        print(f"Model loaded on device: {self.device}")
        self.model.eval()   

    def caption_image(self, image_path: str, prompt: str) -> str:
        """
        Generate detailed caption for a single image using InstructBLIP-XL
        """
        
        try:
            image = Image.open(image_path).convert('RGB')
            
            # Format the prompt properly for Qwen VL
            formatted_prompt = f"<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>{prompt}<|im_end|>\n<|im_start|>assistant\n"
            
            inputs = self.processor(
                images=image, 
                text=formatted_prompt, 
                return_tensors="pt",
                padding=True
            )
            
            # Move inputs to same device as model
            inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs, 
                    max_new_tokens=250, 
                    do_sample=False,
                    num_beams=1,
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )
        
            # Decode only the new tokens (skip the input prompt)
            input_length = inputs['input_ids'].shape[1]
            generated_text = self.processor.decode(generated_ids[0][input_length:], skip_special_tokens=True)
            return generated_text.strip()
            
        except Exception as e:
            print(f"Error captioning image {image_path}: {e}")
            return "Error generating caption"
    
   
    
    def caption_frames(self, frame_data: List[tuple], prompt: str) -> List[Dict[str, Any]]:
        """
        frame_data: List of (timestamp, frame_path, frame_array) tuples
        """
        
        captioned_frames = []
        
        for i in range(0, len(frame_data)):
            img = frame_data[i][1] # path to image
            caption = self.caption_image(img, prompt)
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