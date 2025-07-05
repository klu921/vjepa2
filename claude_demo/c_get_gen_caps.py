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
        Look at the frame from left to right, bottom to top. Write in the following form:
        
        Objects: Describe all the items and people you see in detail: their colors, textures, purposes, etc
        Spatial Layout: The relationships between the objects, the actions of the objects if they are moving, how they interact with the environment, etc.
        Motions: Any motions, actions, interactions, humans if there are any. 
        Environment: The environment of the frame, the background, the weather, the time of day, etc.
        Summary: A concise summary of the main idea of theframe. 
        VERY IMPORTANT: YOU ARE ALLOWED TO USE A MAXIMUM OF 400 words in total.

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