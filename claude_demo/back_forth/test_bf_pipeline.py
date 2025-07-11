#!/usr/bin/env python3
"""
Demo Script for Improved Interactive Pipeline

This demonstrates the enhanced pipeline that supports true back-and-forth
interaction without forcing the LLM to give final answers prematurely.
"""

from pandas.io.parsers.base_parser import parsers
from interactive_pipeline import InteractivePipeline
import json
import time
import pandas as pd
import re
from typing import List, Dict, Any

def load_spatial_reasoning_dataset(dataset_path: str = "spatial_reasoning_dataset.csv") -> List[Dict]:
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

def test_pipeline():
    """Demonstrate the improved iterative interaction capabilities"""
    
    
    pipeline = InteractivePipeline(
        llm_model="deepseek-ai/DeepSeek-V3",
        frame_selector_model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", 
        vlm_model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        log_file="enhanced_demo.log"
    )
    print("pipeline initialized")
    print()
    
    # Demo question that requires thorough investigation
    questions = load_spatial_reasoning_dataset()
   
    with open("answers.txt", "w") as f:
        pass
    # Process the question
    for i, question in enumerate(questions):
        start_time = time.time()

        with open("enhanced_demo.log", "a") as f:
            f.write(f"Q: {question['question']}\n")
            f.write(f"Choices: {question['choices']}\n")
            f.write(f"Task: {question['task']}\n")
            f.write(f"Video UID: {question['video_uid']}\n")
            f.write(f"=" * 50 + "\n")
            f.flush()

        print(f"Question {i+1}:")

        result = pipeline.process_mcq(question['question'], question['choices'])
        processing_time = time.time() - start_time
    
        # Display results
        print("\n" + "=" * 50)
        print("INTERACTION RESULTS")
        print("=" * 50)
        print(f"Final Answer: {result['answer']}")
        with open("answers.txt", "a") as f:
            f.write(f"Question {i+1}:\n")
            f.write(f"Final Answer: {result['answer']}\n \n")
            f.flush()
        print(f"Total Processing Time: {processing_time:.1f} seconds")
        print(f"Conversation Iterations: {result.get('iterations', 'N/A')}")


if __name__ == "__main__":
    test_pipeline()
