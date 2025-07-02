#!/usr/bin/env python3
"""
Automatic Spatial Reasoning Evaluation Script
Regenerates captions with InstructBLIP and evaluates on spatial reasoning dataset
"""

import os
import sys
from video_understanding_framework import VideoUnderstandingFramework
from video_qa_system import VideoQASystem
import json
import time

def main():
    print("=== Automatic Spatial Reasoning Evaluation ===")
    
    # Check if we need to regenerate captions with InstructBLIP
    captions_file = "data/video_captions_instructblip.json"
    
    if not os.path.exists(captions_file):
        print("Regenerating captions with InstructBLIP...")
        
        # Initialize framework with video
        framework = VideoUnderstandingFramework("video.mp4")
        
        # Process first 20 frames for quick testing (you can change this)
        print("Processing subset of frames for testing...")
        
        # Extract frames (will use existing ones)
        framework.frame_extractor = framework.VideoFrameExtractor(framework.video_path, framework.frames_dir)
        frame_files = sorted([f for f in os.listdir(framework.frames_dir) if f.endswith('.jpg')])[:20]  # Limit for testing
        
        frames_data = []
        for frame_file in frame_files:
            frame_path = os.path.join(framework.frames_dir, frame_file)
            try:
                timestamp = float(frame_file.replace('frame_', '').replace('s.jpg', ''))
            except:
                timestamp = 0.0
            frames_data.append((timestamp, frame_path, None))
        
        print(f"Processing {len(frames_data)} frames...")
        
        # Generate captions with InstructBLIP
        from image_captioner import ImageCaptioner
        captioner = ImageCaptioner()  # Now uses InstructBLIP
        captioned_frames = captioner.batch_caption_frames(frames_data)
        
        # Save captions
        captioner.save_captions(captioned_frames, captions_file)
        print(f"Saved captions to {captions_file}")
    else:
        print(f"Using existing captions from {captions_file}")
    
    # Initialize QA system with the captions
    print("Initializing QA system...")
    qa_system = VideoQASystem(captions_file)
    
    # Run spatial reasoning evaluation
    print("Running spatial reasoning evaluation...")
    eval_results = qa_system.evaluate_on_dataset("spatial_reasoning_dataset.csv")
    
    if 'error' not in eval_results:
        print(f"\n=== EVALUATION RESULTS ===")
        print(f"Total Questions: {eval_results['total_questions']}")
        print(f"Correct Answers: {eval_results['correct_answers']}")
        print(f"Overall Accuracy: {eval_results['overall_accuracy']:.2%}")
        
        print(f"\nAccuracy by Task Type:")
        for task, acc in eval_results['task_accuracies'].items():
            print(f"  {task}: {acc:.2%}")
        
        # Show some example results
        print(f"\n=== SAMPLE RESULTS ===")
        for i, result in enumerate(eval_results['detailed_results'][:5]):
            print(f"\nQuestion {i+1}: {result['question']}")
            print(f"Predicted: {result.get('predicted_answer', 'N/A')}")
            print(f"Correct: {result.get('correct_answer', 'N/A')}")
            print(f"Status: {'✓' if result.get('is_correct', False) else '✗'}")
        
        # Save detailed results
        results_file = "spatial_evaluation_results.json"
        with open(results_file, 'w') as f:
            json.dump(eval_results, f, indent=2)
        print(f"\nDetailed results saved to {results_file}")
        
    else:
        print(f"Error in evaluation: {eval_results['error']}")

if __name__ == "__main__":
    main()