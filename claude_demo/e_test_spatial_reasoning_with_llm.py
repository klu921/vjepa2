#!/usr/bin/env python3
"""
Test spatial reasoning using LLM with video captions
Compares the LLM approach vs the existing similarity-based approach
"""

import pandas as pd
import json
from d_llm_mcq_answerer import LLMMCQAnswerer, load_video_captions
from typing import List, Dict, Any
import re

def load_spatial_reasoning_dataset(dataset_path: str = "question_set/spatial_reasoning_dataset.csv") -> List[Dict]:
    """Load and parse spatial reasoning questions from CSV"""
    df = pd.read_csv(dataset_path)
    
    questions = []
    
    for _, row in df.iterrows():
        task = row.get('task', '')
        mcq_text = row.get('mcq_test', '')
        choice_pattern = r'([A-E])\.\s*([^\n]+)'
        matches = re.findall(choice_pattern, mcq_text, re.DOTALL)
        
        choices = [match[1].strip() for match in matches]

        
        questions.append({
            'qid': row.get('qid', ''),
            'question': row.get('question', ''),
            'choices': choices,
            'task': task,
            'video_uid': row.get('video_uid', '')
        })
    
    return questions

def test_llm_mcq_answerer():
        
    # Load dataset and captions
    questions = load_spatial_reasoning_dataset()
    captions = load_video_captions()
    
    print(f"Loaded {len(questions)} questions and {len(captions)} captions")
    
    try:
        llm_answerer = LLMMCQAnswerer("mistralai/Mistral-7B-Instruct-v0.1")
    except Exception as e:
        print(f"Failed to initialize LLM: {e}")
        return
            
    results = []
    
    # Open file to write answers
    with open("key_frames.txt", "a") as key_frames_file:

        with open("Answers.txt", "w") as answers_file:
            answers_file.write("LLM Spatial Reasoning Answers and Reasoning\n")
            answers_file.write("=" * 60 + "\n\n") #for formatting
            
            for i, q in enumerate(questions):
                print(f"\n{'='*60}") #for formatting
                print(f"Question {i+1}/{len(questions)}")
                print(f"Task: {q['task']}")
                print(f"Q: {q['question']}")
                print(f"Choices:")
                for j, choice in enumerate(q['choices']):
                    print(f"  {chr(65+j)}. {choice}")
                
                # Write to file
                answers_file.write(f"Question {i+1}/{len(questions)}\n")
                answers_file.write(f"Task: {q['task']}\n")
                answers_file.write(f"Q: {q['question']}\n")
                answers_file.write("Choices:\n")
                for j, choice in enumerate(q['choices']):
                    answers_file.write(f"  {chr(65+j)}. {choice}\n")
                answers_file.write("\n")
                
                try:
                    # Use enhanced LLM workflow to answer
                    key_frames_file.write(f"key frames for question: {q['question']}\n")
                    key_frames_file.write("=" * 60 + "\n\n")
                    
                    result = llm_answerer.answer_mcq_with_enhanced_workflow(
                        question=q['question'],
                        choices=q['choices'],
                        captions=captions,
                        k=3  # Use top 3 most relevant frames
                    )
                    
                    result.update({
                        'qid': q['qid'],
                        'question': q['question'],
                        'task': q['task']
                    })
                    
                    results.append(result)
                    
                    # Show brief result
                    print(f"\nLLM Answer: {result['predicted_answer']}")
                    print(f"LLM Full Reasoning:\n{result['reasoning']}")
                    
                    # Write detailed result to file
                    answers_file.write(f"LLM Answer: {result['predicted_answer']}\n")
                    answers_file.write("LLM Full Reasoning:\n")
                    answers_file.write(f"{result['reasoning']}\n")
                    answers_file.write("\n" + "="*60 + "\n\n")
                    
                except Exception as e:
                    print(f"  ERROR: {e}")
                    answers_file.write(f"ERROR: {e}\n")
                    answers_file.write("\n" + "="*60 + "\n\n")
                    continue
    
    # Print summary
    print(f"\n=== LLM Results Summary ===")
    print(f"Total questions processed: {len(results)}")
    
    # Task breakdown
    task_counts = {}
    for result in results:
        task = result['task']
        task_counts[task] = task_counts.get(task, 0) + 1
    
    print("\nTask Breakdown:")
    for task, count in task_counts.items():
        print(f"  {task}: {count} questions")
    
    print(f"\nAll answers and reasoning have been saved to 'Answers.txt'")

if __name__ == "__main__":
    test_llm_mcq_answerer()