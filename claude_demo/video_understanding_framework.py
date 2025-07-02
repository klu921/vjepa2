#!/usr/bin/env python3
"""
Video Understanding Framework
A complete system for extracting frames, generating captions, and answering questions about videos
"""

import os
import sys
from typing import List, Dict, Any
from video_frame_extractor import VideoFrameExtractor
from image_captioner import ImageCaptioner
from video_qa_system import VideoQASystem
import json
import time

from transformers import AutoProcessor, AutoModelForImageTextToText

class VideoUnderstandingFramework:
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
        self.qa_system = None
        
        # Data storage
        self.frames_data = []
        self.captioned_frames = []
        
    def process_video(self, interval_seconds: int = 3, save_captions: bool = True) -> bool:
        """
        Complete video processing pipeline:
        1. Extract frames
        2. Generate captions
        3. Save results
        """
        print(f"Starting video processing for: {self.video_path}")
        
        # Step 1: Extract frames
        print("\n=== STEP 1: Extracting Frames ===")
        try:
            self.frame_extractor = VideoFrameExtractor(self.video_path, self.frames_dir)
            video_info = self.frame_extractor.get_frame_info()
            print(f"Video duration: {video_info['duration']:.2f} seconds")
            print(f"Video resolution: {video_info['width']}x{video_info['height']}")
            
            # Check if frames directory is empty or doesn't exist
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
                print(f"Loaded {len(self.frames_data)} existing frames")

            print(f"Extracted {len(self.frames_data)} frames")
            
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return False
        
        # Step 2: Generate captions
        print("\n=== STEP 2: Generating Captions ===")
        try:
            self.captioner = ImageCaptioner()
            self.captioned_frames = self.captioner.batch_caption_frames(self.frames_data)
            
            if save_captions:
                self.captioner.save_captions(self.captioned_frames, self.captions_file)
            
        except Exception as e:
            print(f"Error generating captions: {e}")
            return False
        
        # Step 3: Initialize QA system
        print("\n=== STEP 3: Initializing QA System ===")
        try:
            self.qa_system = VideoQASystem(self.captions_file)
            print("QA system ready for questions!")
            
        except Exception as e:
            print(f"Error initializing QA system: {e}")
            return False
        
        return True
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Ask a question about the video
        """
        if not self.qa_system:
            return {"error": "QA system not initialized. Run process_video() first."}
        
        return self.qa_system.answer_question(question)
    
    def ask_multiple_choice(self, question: str, choices: List[str]) -> Dict[str, Any]:
        """
        Ask a multiple choice question about the video
        """
        if not self.qa_system:
            return {"error": "QA system not initialized. Run process_video() first."}
        
        return self.qa_system.answer_multiple_choice(question, choices)
    
    def get_timeline(self) -> List[Dict]:
        """
        Get a timeline summary of the video
        """
        if not self.qa_system:
            return []
        
        return self.qa_system.get_timeline_summary()
    
    def interactive_mode(self):
        """
        Enter interactive question-answering mode
        """
        if not self.qa_system:
            print("Error: QA system not initialized. Run process_video() first.")
            return
        
        print("\n=== Interactive Video Q&A Mode ===")
        print("Ask questions about the video! Type 'quit' to exit.")
        print("Type 'timeline' to see a summary of the video.")
        print("For multiple choice, use format: 'question? A) choice1 B) choice2 C) choice3'")
        
        while True:
            try:
                question = input("\nYour question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if question.lower() == 'timeline':
                    timeline = self.get_timeline()
                    print("\n=== Video Timeline ===")
                    for item in timeline:
                        print(f"{item['timestamp']:.1f}s: {item['summary']}")
                    continue
                
                # Check if it's multiple choice format
                if ')' in question and any(letter in question for letter in ['A)', 'B)', 'C)', 'D)']):
                    # Parse multiple choice question
                    parts = question.split('?', 1)
                    if len(parts) == 2:
                        q = parts[0].strip() + '?'
                        choices_text = parts[1].strip()
                        
                        # Extract choices
                        choices = []
                        for letter in ['A)', 'B)', 'C)', 'D)', 'E)']:
                            if letter in choices_text:
                                start_idx = choices_text.find(letter) + len(letter)
                                end_idx = choices_text.find(letter[0].replace(')', chr(ord(letter[0]) + 1)) + ')')
                                if end_idx == -1:
                                    choice = choices_text[start_idx:].strip()
                                else:
                                    choice = choices_text[start_idx:end_idx].strip()
                                choices.append(choice)
                        
                        if choices:
                            result = self.ask_multiple_choice(q, choices)
                            print(f"\nAnswer: {result['selected_choice']}")
                            print(f"Reasoning: {result['reasoning']}")
                            print(f"Confidence: {result['confidence']:.2f}")
                            continue
                
                # Regular question
                result = self.ask_question(question)
                
                if 'error' in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"\nAnswer: {result['answer']}")
                    print(f"Confidence: {result['confidence']:.2f}")
                    if result['relevant_frames']:
                        print("Relevant timestamps:", 
                              [f"{f['timestamp']:.1f}s" for f in result['relevant_frames']])
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error processing question: {e}")
        
        print("Goodbye!")

def main():
    """
    Main function to run the video understanding framework
    """
    video_path = "video.mp4"
    
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found in current directory")
        return
    
    # Initialize framework
    framework = VideoUnderstandingFramework(video_path)
    
    # Process video
    print("Processing video... This may take a while depending on video length.")
    success = framework.process_video(interval_seconds=3)
    
    if not success:
        print("Failed to process video")
        return
    
    # Enter interactive mode
    framework.interactive_mode()

if __name__ == "__main__":
    main()