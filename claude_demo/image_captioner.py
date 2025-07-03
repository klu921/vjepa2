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
        # Check which GPUs are actually free (not being used by other processes)
        self.available_gpus = self._get_free_gpus()
        self.num_gpus = len(self.available_gpus)
        
        if self.num_gpus > 0:
            # Use the first available GPU as primary device
            self.device = torch.device(f"cuda:{self.available_gpus[0]}")
            print(f"Using primary device: {self.device}")
            print(f"Available free GPUs: {self.available_gpus} (total: {self.num_gpus})")
            
            # Display free GPU info
            for gpu_id in self.available_gpus:
                gpu_name = torch.cuda.get_device_name(gpu_id)
                gpu_memory = torch.cuda.get_device_properties(gpu_id).total_memory / 1e9
                print(f"  GPU {gpu_id}: {gpu_name} ({gpu_memory:.1f}GB) - FREE")
        else:
            self.device = torch.device("cpu")
            print("No free GPUs available, using CPU")
        
        self.processor = InstructBlipProcessor.from_pretrained(model_name, cache_dir=CACHE_DIR)
        self.model = InstructBlipForConditionalGeneration.from_pretrained(model_name, cache_dir=CACHE_DIR)
        
        # Enable multi-GPU processing only on free GPUs
        if self.num_gpus > 1:
            print(f"Enabling DataParallel across {self.num_gpus} free GPUs: {self.available_gpus}")
            self.model = torch.nn.DataParallel(self.model, device_ids=self.available_gpus)
            self.is_multi_gpu = True
        else:
            self.is_multi_gpu = False
        
        self.model.to(self.device)
        print(f"Loaded model: {model_name} (Multi-GPU: {self.is_multi_gpu})")
    
    def _get_free_gpus(self):
        """Detect which GPUs are free (have minimal memory usage)"""
        free_gpus = []
        
        if not torch.cuda.is_available():
            return free_gpus
        
        for i in range(torch.cuda.device_count()):
            try:
                # Check memory usage
                torch.cuda.set_device(i)
                allocated = torch.cuda.memory_allocated(i)
                reserved = torch.cuda.memory_reserved(i)
                total = torch.cuda.get_device_properties(i).total_memory
                
                # Consider GPU free if less than 10% memory is used
                usage_percent = (allocated + reserved) / total
                
                if usage_percent < 0.1:  # Less than 10% used
                    free_gpus.append(i)
                else:
                    print(f"  GPU {i}: {usage_percent*100:.1f}% used - OCCUPIED")
                    
            except Exception as e:
                print(f"  GPU {i}: Error checking - {e}")
                continue
        
        return free_gpus
    
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
    
    def batch_caption_frames(self, frame_data: List[tuple], batch_size: int = None) -> List[Dict[str, Any]]:
        """
        Caption all frames with comprehensive details using efficient multi-GPU batching
        frame_data: List of (timestamp, frame_path, frame_array) tuples
        batch_size: Number of images to process in parallel (auto-calculated based on GPU count)
        """
        # Auto-calculate optimal batch size based on available GPUs
        if batch_size is None:
            if self.num_gpus > 1:
                # With multi-GPU, we can handle larger batches
                batch_size = self.num_gpus * 4  # 4 images per GPU
                print(f"Auto-selected batch size: {batch_size} (4 per GPU × {self.num_gpus} GPUs)")
            else:
                batch_size = 4  # Conservative for single GPU
                print(f"Auto-selected batch size: {batch_size} (single GPU)")
        else:
            print(f"Using specified batch size: {batch_size}")
        
        captioned_frames = []
        
        # Process frames in batches for better GPU utilization
        for i in range(0, len(frame_data), batch_size):
            batch = frame_data[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(frame_data) + batch_size - 1)//batch_size} ({len(batch)} frames)")
            
            # Load all images in batch
            batch_images = []
            batch_info = []
            
            for timestamp, frame_path, _ in batch:
                try:
                    image = Image.open(frame_path).convert('RGB')
                    batch_images.append(image)
                    batch_info.append((timestamp, frame_path))
                except Exception as e:
                    print(f"Error loading {frame_path}: {e}")
                    continue
            
            if not batch_images:
                continue
            
            # Process this batch with all prompts
            batch_results = self._process_image_batch(batch_images, batch_info)
            captioned_frames.extend(batch_results)
        
        return captioned_frames
    
    def _process_image_batch(self, images: List[Image.Image], frame_info: List[tuple]) -> List[Dict[str, Any]]:
        """Process a batch of images with all prompts efficiently"""
        prompts = [
            "Describe this image in detail, including all objects, people, and activities:",
            "What are the people doing in this image? Describe their actions and interactions:",
            "Describe the setting, environment, and background of this image:",
            "What objects can you see in this image? List them and their locations:",
            "Describe any text, signs, or written content visible in this image:",
            "Generate captions for a spatial intelligence task, where questions will ask about navigation, location, and orientation.",
            "What are the layouts, relationships between objects, proximity of objects to each other and users, and other spatial properties of this image?"
        ]
        
        batch_results = []
        
        # Process general captions (no prompt) in batch
        print("  Processing general captions...")
        general_captions = self._batch_process_with_prompt(images, "Describe this image in detail.")
        
        # Process each detailed prompt in batch
        detailed_caption_sets = {}
        for i, prompt in enumerate(prompts):
            print(f"  Processing detailed prompt {i+1}/{len(prompts)}...")
            detailed_caption_sets[f'detailed_{i+1}'] = self._batch_process_with_prompt(images, prompt)
            
            # Show GPU utilization periodically
            if i == 0 and self.num_gpus > 1:  # Show after first prompt
                self.check_gpu_utilization()
        
        # Combine results
        for idx, (timestamp, frame_path) in enumerate(frame_info):
            captions = {
                'general': general_captions[idx] if idx < len(general_captions) else "Error"
            }
            
            for key, caption_list in detailed_caption_sets.items():
                captions[key] = caption_list[idx] if idx < len(caption_list) else "Error"
            
            batch_results.append({
                'timestamp': timestamp,
                'frame_path': frame_path,
                'captions': captions
            })
        
        return batch_results
    
    def check_gpu_utilization(self):
        """Check current GPU memory usage"""
        if self.num_gpus > 0:
            print("GPU Memory Usage:")
            for i in range(self.num_gpus):
                allocated = torch.cuda.memory_allocated(i) / 1e9
                cached = torch.cuda.memory_reserved(i) / 1e9
                total = torch.cuda.get_device_properties(i).total_memory / 1e9
                print(f"  GPU {i}: {allocated:.1f}GB allocated, {cached:.1f}GB cached, {total:.1f}GB total")
    
    def _batch_process_with_prompt(self, images: List[Image.Image], prompt: str) -> List[str]:
        """Process a batch of images with the same prompt"""
        try:
            # Prepare batch inputs
            prompts = [prompt] * len(images)
            inputs = self.processor(
                images=images, 
                text=prompts, 
                return_tensors="pt", 
                padding=True,
                truncation=True
            ).to(self.device)
            
            with torch.no_grad():
                # Handle DataParallel wrapper
                model_to_use = self.model.module if self.is_multi_gpu else self.model
                generated_ids = model_to_use.generate(
                    **inputs,
                    max_new_tokens=150,
                    do_sample=False,
                    num_beams=2,  # Reduced for faster processing
                    pad_token_id=self.processor.tokenizer.pad_token_id
                )
            
            # Decode all captions at once
            captions = self.processor.batch_decode(generated_ids, skip_special_tokens=True)
            return captions
            
        except Exception as e:
            print(f"Batch processing failed: {e}")
            # Fallback to individual processing
            return [self.caption_image_direct(img, prompt) for img in images]
    
    def caption_image_direct(self, image: Image.Image, prompt: str) -> str:
        """Process single image directly (fallback method)"""
        try:
            inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device)
            
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
            return f"Error: {e}"
    
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