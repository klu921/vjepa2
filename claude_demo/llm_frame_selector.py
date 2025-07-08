#!/usr/bin/env python3
"""
LLM Frame Selector - Uses reasoning LLM to analyze all captions and select key frames

This module implements the pipeline step where an LLM analyzes all general captions,
considers the question and answer choices, and intelligently selects the most relevant
key frames for final answer generation.
"""

import json
from typing import List, Dict, Any
from together import Together

client = Together()

class LLMFrameSelector:
    def __init__(self, model_name: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"):
        """
        Initialize the LLM Frame Selector
        
        Args:
            model_name: The reasoning LLM model to use for frame selection
        """
        self.model_name = model_name
        
    def select_key_frames(self, 
                         captions: List[Dict], 
                         question: str, 
                         answer_choices: List[str],
                         max_frames: int = 5) -> List[Dict]:
        """
        Use LLM reasoning to select the most relevant frames for answering the question
        
        Args:
            captions: List of all caption dictionaries with frame info
            question: The question to answer
            answer_choices: List of possible answer choices
            max_frames: Maximum number of frames to select
            
        Returns:
            List of selected key frame dictionaries
        """
        # Create the reasoning prompt
        prompt = self._create_frame_selection_prompt(captions, question, answer_choices, max_frames)
        
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
                stream=False
            )
            
            response_text = response.choices[0].message.content
            
            # Parse the response to extract selected frame indices
            selected_indices = self._parse_frame_selection(response_text, len(captions))
            
            # Return the selected frames
            selected_frames = [captions[i] for i in selected_indices if i < len(captions)]
            
            print(f"LLM selected {len(selected_frames)} key frames from {len(captions)} total frames")
            print(f"Selected frame timestamps: {[f['timestamp'] for f in selected_frames]}")
            
            return selected_frames
            
        except Exception as e:
            print(f"Error in LLM frame selection: {e}")
            # Fallback to first few frames if LLM fails
            return captions[:max_frames]
    
    def _create_frame_selection_prompt(self, 
                                     captions: List[Dict], 
                                     question: str, 
                                     answer_choices: List[str],
                                     max_frames: int) -> str:
        """
        Create a detailed prompt for the LLM to analyze captions and select key frames
        """
        # Format all captions with timestamps
        captions_text = ""
        for i, cap_data in enumerate(captions):
            timestamp = cap_data.get('timestamp', 0)
            caption = cap_data.get('captions', '')
            captions_text += f"Frame {i+1} (at {timestamp:.1f}s):\n{caption}\n\n"
        
        # Format answer choices
        choices_text = ""
        for i, choice in enumerate(answer_choices):
            choices_text += f"{chr(65+i)}. {choice}\n"
        
        prompt = f"""You are an expert video analyst. You need to analyze video frame captions and select the most relevant frames to answer a specific question.

VIDEO FRAME CAPTIONS:
{captions_text}

QUESTION TO ANSWER:
{question}

ANSWER CHOICES:
{choices_text}

TASK:
Carefully analyze each frame caption and determine which frames contain information most relevant to answering the question. Consider:

1. Which frames show objects, actions, or spatial relationships mentioned in the question?
2. Which frames provide evidence that could help distinguish between the answer choices?
3. Which frames show the key visual elements needed to make a decision?

You should select AT MOST {max_frames} frames, but try to keep it minimal - only choose frames that are truly essential for answering the question.

RESPONSE FORMAT:
First, provide your reasoning for each potentially relevant frame. Then, clearly list your final selection.

Reasoning:
[Analyze each relevant frame and explain why it might be useful]

Selected Frames:
[List the frame numbers (1, 2, 3, etc.) of your final selection, separated by commas]

Example: Selected Frames: 1, 5, 12
"""
        
        return prompt
    
    def _parse_frame_selection(self, response_text: str, total_frames: int) -> List[int]:
        """
        Parse the LLM response to extract selected frame indices
        
        Args:
            response_text: The LLM's response
            total_frames: Total number of available frames
            
        Returns:
            List of selected frame indices (0-based)
        """
        selected_indices = []
        
        # Look for "Selected Frames:" section
        lines = response_text.split('\n')
        for line in lines:
            if 'Selected Frames:' in line:
                # Extract frame numbers
                frame_part = line.split('Selected Frames:')[1].strip()
                # Parse comma-separated numbers
                try:
                    frame_numbers = [int(x.strip()) for x in frame_part.split(',') if x.strip().isdigit()]
                    # Convert to 0-based indices
                    selected_indices = [max(0, f-1) for f in frame_numbers if 1 <= f <= total_frames]
                    break
                except ValueError:
                    continue
        
        # Fallback: if no valid selection found, look for any numbers in the response
        if not selected_indices:
            import re
            numbers = re.findall(r'\b(\d+)\b', response_text)
            for num_str in numbers:
                num = int(num_str)
                if 1 <= num <= total_frames:
                    idx = num - 1
                    if idx not in selected_indices:
                        selected_indices.append(idx)
                        if len(selected_indices) >= 5:  # Limit fallback selection
                            break
        
        # Final fallback: select first few frames
        if not selected_indices:
            selected_indices = list(range(min(3, total_frames)))
        
        return selected_indices[:5]  # Ensure we don't exceed max frames

def test_frame_selector():
    """Test the frame selector with sample data"""
    # Load existing captions
    try:
        with open('captions/video_captions.json', 'r') as f:
            captions = json.load(f)
        
        # Test with a sample question
        question = "What technology does the person interact with?"
        choices = [
            "Mobile phone and television",
            "Computer and tablet", 
            "Smart home system and microwave",
            "Robot vacuum and speaker"
        ]
        
        selector = LLMFrameSelector()
        selected_frames = selector.select_key_frames(captions[:20], question, choices, max_frames=3)
        
        print(f"Test completed: Selected {len(selected_frames)} frames")
        for frame in selected_frames:
            print(f"Frame at {frame['timestamp']:.1f}s: {frame['captions'][:100]}...")
            
    except FileNotFoundError:
        print("No captions file found. Run caption generation first.")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_frame_selector()