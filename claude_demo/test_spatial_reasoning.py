#!/usr/bin/env python3
"""
Quick Spatial Reasoning Test
Uses existing captions to test spatial reasoning questions
"""

from video_qa_system import VideoQASystem
import json

def main():
    print("=== Testing Spatial Reasoning with Existing Captions ===")
    
    # Try both caption files
    captions_files = [
        "data/video_captions.json",
        "data/video_captions_instructblip.json"
    ]
    
    for captions_file in captions_files:
        try:
            print(f"\nTesting with: {captions_file}")
            qa_system = VideoQASystem(captions_file)
            
            # Run evaluation
            eval_results = qa_system.evaluate_on_dataset("spatial_reasoning_dataset.csv")
            
            if 'error' not in eval_results:
                print(f"Overall Accuracy: {eval_results['overall_accuracy']:.2%}")
                print(f"Total Questions: {eval_results['total_questions']}")
                
                print("Task Accuracies:")
                for task, acc in eval_results['task_accuracies'].items():
                    print(f"  {task}: {acc:.2%}")
                
                # Show sample questions and answers
                print("\nSample Results:")
                for i, result in enumerate(eval_results['detailed_results'][:3]):
                    status = "✓" if result.get('is_correct', False) else "✗"
                    print(f"{status} Q: {result['question']}")
                    print(f"  Predicted: {result.get('predicted_answer', 'N/A')}")
                    print(f"  Correct: {result.get('correct_answer', 'N/A')}")
                    print()
                
                break  # Use first working file
            else:
                print(f"Error: {eval_results['error']}")
                
        except Exception as e:
            print(f"Could not use {captions_file}: {e}")
            continue

if __name__ == "__main__":
    main()