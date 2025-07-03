import cv2
import os
from typing import List, Tuple
import numpy as np
from PIL import Image

class VideoFrameExtractor:
    def __init__(self, video_path: str, output_dir: str = "data/frames"):
        self.video_path = video_path
        self.output_dir = output_dir
        self.frames_data = []
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def extract_frames(self, interval_seconds: int = 3) -> List[Tuple[float, str, np.ndarray]]:
        """
        Extract frames from video at specified intervals
        Returns: List of (timestamp, frame_path, frame_array) tuples
        """
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval_seconds)
        
        frame_count = 0
        extracted_frames = []
        
        print(f"Video FPS: {fps}")
        print(f"Extracting frames every {interval_seconds} seconds (every {frame_interval} frames)")
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                
                # Convert BGR to RGB for PIL
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Save frame
                frame_filename = f"frame_{timestamp:.04d}s.jpg"
                frame_path = os.path.join(self.output_dir, frame_filename)
                
                pil_image = Image.fromarray(frame_rgb)
                pil_image.save(frame_path, quality=95)
                
                extracted_frames.append((timestamp, frame_path, frame_rgb))
                print(f"Extracted frame at {timestamp:.2f}s")
            
            frame_count += 1
        
        cap.release()
        self.frames_data = extracted_frames
        return extracted_frames
    
    def get_frame_info(self) -> dict:
        """Get video information"""
        cap = cv2.VideoCapture(self.video_path)
        
        info = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
        
        cap.release()
        return info

if __name__ == "__main__":
    extractor = VideoFrameExtractor("video.mp4")
    info = extractor.get_frame_info()
    print("Video Info:", info)
    
    frames = extractor.extract_frames(interval_seconds=3)
    print(f"Extracted {len(frames)} frames")