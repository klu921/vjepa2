#!/usr/bin/env python3
"""
Test script for the Video Understanding Framework
Tests with a shorter segment of the video for demonstration
"""

import cv2
import os
from video_understanding_framework import VideoUnderstandingFramework

def create_test_video_segment(input_path: str, output_path: str, duration_seconds: int = 30):
    """
    Create a shorter test segment from the original video
    """
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open {input_path}")
        return False
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    max_frames = int(fps * duration_seconds)
    
    print(f"Creating {duration_seconds}s test video from {input_path}")
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        out.write(frame)
        frame_count += 1
    
    cap.release()
    out.release()
    
    print(f"Created test video: {output_path}")
    return True

def test_framework():
    """
    Test the complete framework with a short video segment
    """
    # Create test video segment
    test_video_path = "data/test_video.mp4"
    
    if not os.path.exists(test_video_path):
        print("Creating test video segment...")
        if not create_test_video_segment("video.mp4", test_video_path, 30):
            print("Failed to create test video")
            return
    
    # Test the framework
    print("\n=== Testing Video Understanding Framework ===")
    
    try:
        # Initialize framework
        framework = VideoUnderstandingFramework(test_video_path)
        
        # Process video
        print("Processing test video...")
        success = framework.process_video(interval_seconds=5)  # Every 5 seconds for faster testing
        
        if not success:
            print("Failed to process video")
            return
        
        # Test questions
        test_questions = [
            "What do you see in this video?",
            "What is the person doing?",
            "What objects are visible?",
            "Describe the setting or environment"
        ]
        
        print("\n=== Testing Questions ===")
        for question in test_questions:
            print(f"\nQ: {question}")
            result = framework.ask_question(question)
            
            if 'error' not in result:
                print(f"A: {result['answer']}")
                print(f"Confidence: {result['confidence']:.2f}")
            else:
                print(f"Error: {result['error']}")
        
        # Test multiple choice
        print("\n=== Testing Multiple Choice ===")
        mc_result = framework.ask_multiple_choice(
            "What type of video is this?",
            ["Tutorial/Educational", "Entertainment", "Documentation", "Personal/Vlog"]
        )
        
        if 'error' not in mc_result:
            print(f"Selected: {mc_result['selected_choice']}")
            print(f"Reasoning: {mc_result['reasoning']}")
        
        print("\n=== Framework Test Completed Successfully ===")
        
    except Exception as e:
        print(f"Error testing framework: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_framework()