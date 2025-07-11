#!/usr/bin/env python3
"""
Organize Question Frames - Extract key frames and organize them by question

This program:
1. Parses question_set/key_frames.txt to extract question info and selected frame timestamps
2. Parses Answers.txt to extract LLM answers and reasoning
3. Copies corresponding frame images to question-specific folders
4. Creates summary text files for each question
"""

import os
import shutil
import re
from typing import Dict, List, Tuple, Optional

def parse_key_frames_file(file_path: str) -> Dict[int, Dict]:
    """Parse key_frames.txt to extract question info and selected frame timestamps"""
    questions = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by the specific pattern that separates questions
    # Pattern: ============================================================
    #          
    #          ============================================================
    #           Question X/43
    question_sections = re.split(r'={60,}\n\n={60,}\n Question', content)
    
    # Handle first section (starts with the first question)
    if question_sections and question_sections[0].strip():
        # First section starts with the first question header
        first_section = question_sections[0]
        # Add back the "Question" that was part of the split
        question_sections[0] = first_section
        
        # Handle remaining sections
        for i in range(1, len(question_sections)):
            question_sections[i] = "Question" + question_sections[i]
    
    for section in question_sections:
        if not section.strip():
            continue
            
        # Extract question number
        question_match = re.search(r'Question (\d+)/43', section)
        if not question_match:
            continue
            
        question_num = int(question_match.group(1))
        
        # Extract question text
        question_text_match = re.search(r'Key frames for question: (.+?)\n', section)
        question_text = question_text_match.group(1) if question_text_match else "Question text not found"
        
        # Extract selected frame timestamps
        timestamp_match = re.search(r'Selected frame timestamps: \[([^\]]+)\]', section)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            # Parse timestamps (can be floats)
            timestamps = []
            for ts in timestamp_str.split(','):
                ts = ts.strip()
                if ts:
                    timestamps.append(float(ts))
        else:
            timestamps = []
        
        # Extract the full enhanced caption/reasoning content (everything after "Enhanced caption for frames:")
        enhanced_caption_match = re.search(r'Enhanced caption for frames: (.+?)(?=\n={60,}\n\n={60,}|$)', section, re.DOTALL)
        enhanced_caption = enhanced_caption_match.group(1).strip() if enhanced_caption_match else ""
        
        # If enhanced caption is empty, try to get everything after "Enhanced caption for frames:" until the end
        if not enhanced_caption:
            enhanced_caption_match = re.search(r'Enhanced caption for frames: (.+)', section, re.DOTALL)
            enhanced_caption = enhanced_caption_match.group(1).strip() if enhanced_caption_match else ""
        
        # Also extract the full section content for detailed analysis
        full_section = section.strip()
        
        questions[question_num] = {
            'question_text': question_text,
            'timestamps': timestamps,
            'enhanced_caption': enhanced_caption,
            'full_section': full_section
        }
    
    return questions

def parse_answers_file(file_path: str) -> Dict[int, Dict]:
    """Parse Answers.txt to extract LLM answers and reasoning"""
    answers = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by question sections using the same pattern as key_frames
    question_sections = re.split(r'={60,}', content)
    
    for section in question_sections:
        if not section.strip():
            continue
            
        # Extract question number
        question_match = re.search(r'Question (\d+)/43', section)
        if not question_match:
            continue
            
        question_num = int(question_match.group(1))
        
        # Extract task
        task_match = re.search(r'Task: (.+)', section)
        task = task_match.group(1) if task_match else "Task not found"
        
        # Extract question text
        question_text_match = re.search(r'Q: (.+)', section)
        question_text = question_text_match.group(1) if question_text_match else "Question not found"
        
        # Extract choices
        choices_section = re.search(r'Choices:\n((?:  [A-E]\. .+\n?)+)', section)
        choices = []
        if choices_section:
            choice_lines = choices_section.group(1).strip().split('\n')
            for line in choice_lines:
                line = line.strip()
                if line:
                    choices.append(line)
        
        # Extract LLM answer
        llm_answer_match = re.search(r'LLM Answer: (.+)', section)
        llm_answer = llm_answer_match.group(1) if llm_answer_match else "Answer not found"
        
        # Extract the COMPLETE LLM reasoning - everything after "LLM Full Reasoning:" until the end of the section
        reasoning_match = re.search(r'LLM Full Reasoning:\n(.*?)(?=\n={60,}|$)', section, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else "Reasoning not found"
        
        # If reasoning is empty, try alternative extraction
        if not reasoning or reasoning == "Reasoning not found":
            # Try to get everything after "LLM Full Reasoning:" until the end
            reasoning_match = re.search(r'LLM Full Reasoning:\n(.+)', section, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "Reasoning not found"
        
        answers[question_num] = {
            'task': task,
            'question_text': question_text,
            'choices': choices,
            'llm_answer': llm_answer,
            'reasoning': reasoning
        }
    
    return answers

def timestamp_to_frame_filename(timestamp: float) -> str:
    """Convert timestamp to frame filename format"""
    return f"frame_{timestamp:07.2f}s.jpg"

def copy_frame_files(question_num: int, timestamps: List[float], source_dir: str, dest_dir: str):
    """Copy frame files for a specific question to its folder"""
    os.makedirs(dest_dir, exist_ok=True)
    
    copied_files = []
    for timestamp in timestamps:
        frame_filename = timestamp_to_frame_filename(timestamp)
        source_path = os.path.join(source_dir, frame_filename)
        dest_path = os.path.join(dest_dir, frame_filename)
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            copied_files.append(frame_filename)
            print(f"  Copied: {frame_filename}")
        else:
            print(f"  WARNING: Frame file not found: {frame_filename}")
    
    return copied_files

def create_question_summary(question_num: int, key_frames_data: Dict, answers_data: Dict, 
                          copied_files: List[str], dest_dir: str):
    """Create a comprehensive summary text file for each question"""
    summary_path = os.path.join(dest_dir, f"question_{question_num}_summary.txt")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"QUESTION {question_num} SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        # Basic question info
        if question_num in answers_data:
            answer_info = answers_data[question_num]
            f.write(f"TASK: {answer_info['task']}\n")
            f.write(f"QUESTION: {answer_info['question_text']}\n\n")
            
            f.write("ANSWER CHOICES:\n")
            for choice in answer_info['choices']:
                f.write(f"{choice}\n")
            f.write("\n")
        
        # Key frames info
        if question_num in key_frames_data:
            frames_info = key_frames_data[question_num]
            f.write(f"SELECTED FRAME TIMESTAMPS: {frames_info['timestamps']}\n")
            f.write(f"TOTAL FRAMES SELECTED: {len(frames_info['timestamps'])}\n\n")
            
            f.write("FRAME FILES IN THIS FOLDER:\n")
            for filename in copied_files:
                f.write(f"  {filename}\n")
            f.write("\n")
        
        # LLM answer and reasoning
        if question_num in answers_data:
            answer_info = answers_data[question_num]
            f.write(f"LLM ANSWER: {answer_info['llm_answer']}\n\n")
            
            f.write("FULL LLM REASONING:\n")
            f.write("=" * 50 + "\n")
            f.write(f"{answer_info['reasoning']}\n\n")
        
        # Complete key frames section (includes enhanced captions)
        if question_num in key_frames_data:
            frames_info = key_frames_data[question_num]
            f.write("COMPLETE KEY FRAMES SECTION:\n")
            f.write("=" * 50 + "\n")
            f.write(f"{frames_info['full_section']}\n")

def main():
    """Main function to organize question frames"""
    # Configuration
    key_frames_file = "question_set/key_frames.txt"
    answers_file = "Answers.txt"
    source_frames_dir = "frames"
    dest_base_dir = "set_1_question_frames"
    
    print("Starting question frame organization...")
    print(f"Reading key frames from: {key_frames_file}")
    print(f"Reading answers from: {answers_file}")
    print(f"Source frames directory: {source_frames_dir}")
    print(f"Destination base directory: {dest_base_dir}")
    print()
    
    # Parse input files
    print("Parsing key frames file...")
    key_frames_data = parse_key_frames_file(key_frames_file)
    print(f"Found {len(key_frames_data)} questions in key frames file")
    
    print("Parsing answers file...")
    answers_data = parse_answers_file(answers_file)
    print(f"Found {len(answers_data)} questions in answers file")
    print()
    
    # Process each question
    total_questions = max(len(key_frames_data), len(answers_data))
    for question_num in range(1, total_questions + 1):
        print(f"Processing Question {question_num}...")
        
        question_dir = os.path.join(dest_base_dir, f"question_{question_num}")
        
        # Copy frame files if we have timestamp data
        copied_files = []
        if question_num in key_frames_data:
            timestamps = key_frames_data[question_num]['timestamps']
            print(f"  Found {len(timestamps)} timestamps: {timestamps}")
            copied_files = copy_frame_files(question_num, timestamps, source_frames_dir, question_dir)
        else:
            print(f"  No key frames data found for question {question_num}")
        
        # Create summary file
        create_question_summary(question_num, key_frames_data, answers_data, copied_files, question_dir)
        print(f"  Created summary file in {question_dir}")
        print()
    
    print("Organization complete!")
    print(f"All question folders created in: {dest_base_dir}")

if __name__ == "__main__":
    main()