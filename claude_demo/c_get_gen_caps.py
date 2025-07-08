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
TOGETHER_API_KEY = "c0b5142ff581b2e2a6f64a778d4bd396b419a0bfffc0efbc3bdf635f03b1f3d0"

class get_general_captions:
    def __init__(self, video_path: str):
        """
        Initialize the complete video understanding framework
        """
        self.video_path = video_path
        self.frames_dir = "frames"
        self.captions_file = "captions/video_captions.json"
        
        # Initialize components
        self.frame_extractor = None
        self.captioner = None
        
        # Data storage
        self.frames_data = []
        self.captioned_frames = []

        #TODO: Design the best possible prompt for general captioning that represents the image well
        self.GENERAL_PROMPT = """Please caption this image with EXTREME DETAIL, describing each object comprehensively. For each object, describe: exact colors, materials, textures, shapes, sizes, positions, relationships, conditions, and purposes. Describe all actions, movements, gestures, expressions, and interactions. Describe the complete environment, lighting, atmosphere, spatial layout, and context.

Please format your answer EXACTLY as follows:

Objects:
- [Object 1]: [Extremely detailed description including all visual characteristics, materials, position, relationships, etc.]
- [Object 2]: [Same level of extreme detail]
- [Continue for ALL visible objects]

Actions:
- [Describe ALL actions, movements, gestures, expressions in complete detail]

Setting/context:
- [Describe the complete environment, lighting, atmosphere, spatial layout, context, purpose, etc.]

BE EXTREMELY THOROUGH AND DETAILED in every aspect."""

        self.GENERAL_BATCH_PROMPT = """CRITICAL: You must provide EXTREME DETAIL for each image following this EXACT format. Here is an example of the level of detail required:

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

    def process_video(self, interval_seconds: int = 3, save_captions: bool = True) -> bool:
        """
        1. Extract frames
        2. Generate captions
        3. Save results
        """      
        #extract frames
        frames_need_extraction = False
        try:
            if frames_need_extraction:
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
        
        # generate captions
        print("\n=== STEP 2: Generating Captions ===")
        try:
            self.captioner = ImageCaptioner()
            self.captioned_frames = self.captioner.caption_frames(self.frames_data, self.GENERAL_BATCH_PROMPT, captions_on = True)
            
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