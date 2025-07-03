#!/usr/bin/env python3
"""
Pathway: Video ----frame-extractor ----> frames ----captioner ----> general captions

def __init__(): initialize video path, frame directory, caption file, frame extractor, captioner.
def process_video(): extract frames if they don't already exist, generate captions, save captions.
"""

import os
import sys
from typing import List, Dict, Any
from a_video_frame_extractor import VideoFrameExtractor
from b_image_captioner import ImageCaptioner
import json
import time

from transformers import AutoProcessor, AutoModelForImageTextToText

class get_general_captions:
    def __init__(self, video_path: str):
        """
        Initialize the complete video understanding framework
        """
        self.video_path = video_path
        self.frames_dir = "data/frames"
        self.captions_file = "data/video_captions.json"
        
        # Initialize components
        self.frame_extractor = None
        self.captioner = None
        
        # Data storage
        self.frames_data = []
        self.captioned_frames = []

        #TODO: Design the best possible prompt for general captioning that represents the image well
        self.GENERAL_PROMPT = """
        Step 1: **Scene Context**: Observe the video. What is the primary setting and activity in the video?
        Step 2: **Motion Description**: Identify and describe any significant motion or actions taking place.
        Step 3: **Spatial Relationship Analysis**: Examine and report on the spatial relationships between key objects or characters in the video frames. Describe the positioning and orientation of each element relative to others.
        Step 4: **Detailed Object Analysis**: List the key objects and characters in the frame. Describe their color, shape, texture, and any other notable features with precision. Focus on specific details like clothing, accessories, and colors.
        Step 5: **Temporal Relationship Context**: These video frames are part of a 1-minute sequence, therefore explain any temporal relationships.
        Step 6: **Additional Details**: Note any other important details or elements that stand out but are not covered by the above points, i.e.: gender, hair color, colors of accessories and other attributes in the video frames.
        Step 7: **Summary**: Provide a concise yet comprehensive summary capturing the key elements and takeaways from this 1-minute video following Steps 1 to 6 above. 
        Your caption should encapsulate the scene's key aspects, offering a comprehensive understanding of its environment, activities and context.
        
        Strictly return your results in the following format. Please see the example below:
            "Scene Context": "A busy beach scene with families and surfers enjoying the sunny day.",
            "Motion Description": "Children are building a sandcastle, a dog is running towards the water, and a surfer is catching a wave.",
            "Spatial Relationship Analysis": "The sandcastle is in the foreground, the dog approaches from the left, and the surfer moves from right to center.",
            "Detailed Object Analysis": "Children are wearing colorful swimwear; the dog is a golden retriever; the surfer is wearing a blue and white wetsuit.",
            "Temporal Relationship Context": "The progression from building sandcastles to engaging with the incoming tide indicates a passage of time towards later afternoon.",
            "Additional Details": "One child has red hair; the dog's leash is lying abandoned on the sand; multiple surfboards are visible in the background.",
            "Summary": "The video frames depict a joyful beach day emphasizing family activities, interaction with nature, and surfing as a key activity, showcasing the beach's vibrant atmosphere."
        VERY IMPORTANT: YOU ARE ALLOWED TO USE A MAXIMUM OF 200 words in total.
        """
        
    def process_video(self, interval_seconds: int = 3, save_captions: bool = True) -> bool:
        """
        Complete video processing pipeline:
        1. Extract frames
        2. Generate captions
        3. Save results
        """      
        #extract frames
        try:
            self.frame_extractor = VideoFrameExtractor(self.video_path, self.frames_dir)
            video_info = self.frame_extractor.get_frame_info()

            if not os.path.exists(self.frames_dir) or not os.listdir(self.frames_dir):
                print("Frames directory is empty or doesn't exist. Extracting frames...")
                self.frames_data = self.frame_extractor.extract_frames(interval_seconds)
    
            else:
                print("Frames already exist in directory. Loading existing frames...")
                # Load existing frames from directory
                self.frames_data = []
                for filename in sorted(os.listdir(self.frames_dir)):
                    if filename.endswith(('.jpg', '.jpeg', '.png')):
                        frame_path = os.path.join(self.frames_dir, filename)
                        # Extract timestamp from filename (assuming format like "frame_3.0.jpg")
                        try:
                            timestamp = float(filename.replace('frame_', '').replace('s.jpg', '').replace('s.jpeg', '').replace('s.png', ''))
                        except ValueError:
                            timestamp = 0.0
                        
                        self.frames_data.append((timestamp, frame_path, None))
            print(f"Extracted {len(self.frames_data)} frames")        
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return False
        
        # generate N
        print("\n=== STEP 2: Generating Captions ===")
        try:
            self.captioner = ImageCaptioner()
            self.captioned_frames = self.captioner.caption_frames(self.frames_data, self.GENERAL_PROMPT)
            
            if save_captions:
                self.captioner.save_captions(self.captioned_frames, self.captions_file)
            
        except Exception as e:
            print(f"Error generating captions: {e}")
            return False
        
        return True
    

def main():
    """
    Main function to run the video understanding framework
    """
    video_path = "video/video.mp4"
    
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found in current directory")
        return
    
    # Initialize framework
    framework = get_general_captions(video_path)
    
    # Process video
    print("Processing video... This may take a while depending on video length.")
    success = framework.process_video(interval_seconds=3)
    
    if not success:
        print("Failed to process video")
        return
    

if __name__ == "__main__":
    main()