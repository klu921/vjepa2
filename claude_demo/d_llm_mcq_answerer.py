"""
This file contains the LLM MCQ Answerer.

def __init__(): initialize model, tokenizer, device
def answer_mcq_with_captions(): [question, choices, captions -> answer]
def format_captions(): [list of captions -> formatted captions in frame: timestep: caption]
def create_mcq_prompt(): [question, choices, captions -> structured prompt for LLM to answer]



Need to build:
#TODO: Find best way to get key frames
def get_key_frames(): [list of captions, question -> list of frames]
def gen_specific_prompt(): [question + answer choices -> prompt]

later on:
some measure of confidence in answer, if not we loop back
"""
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, AutoModelForImageTextToText, AutoProcessor
from typing import List, Dict, Any
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from together import Together
from PIL import Image
import time
client = Together()

class LLMMCQAnswerer:

    def __init__(self, model_name: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"):
        
        # Initialize sentence transformer for finding key frames
        self.model_name = model_name
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

    
    def answer_mcq_with_captions(self, 
                                question: str, 
                                choices: List[str], 
                                captions: List[Dict]) -> Dict[str, Any]:
        """
        Answer MCQ using relevant video captions
        
        Args:
            question: The question to answer
            choices: List of answer choices (A, B, C, D, etc.)
            relevant_captions: List of caption dictionaries with frame info
        
        Returns:
            Dict with predicted answer, confidence, and reasoning
        """
        # Format captions, prompt for the model
        caption_text = self._format_captions(captions) #
        prompt = self._create_mcq_prompt(question, choices, caption_text) #creates a well-structured prompt
        with open("prompt.txt", "w") as f:
            f.write(prompt)

        attempts = 6
        for i in range(attempts):
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", 
                        "content": prompt}
                    ],
                    stream = False
                )
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(10)
                continue


        response = response.choices[0].message.content
        
        predicted_answer = ""
        try:
            predicted_answer = response.split("The correct answer is: ")[1]
        except IndexError:
            predicted_answer = "No answer found"
        
        return {
            "predicted_answer": predicted_answer,
            "reasoning": response
        }
        
    
    def _format_captions(self, captions: List[Dict]) -> str:
        """append all general captions into a single string for the model"""
        formatted = []
        
        for i, cap_data in enumerate(captions):
            timestamp = cap_data.get('timestamp', 0)
            caption_text = cap_data.get('captions', '')
            # Caption text is a single string, not a list or dict
            formatted.append(f"Frame {i+1} (at {timestamp:.1f}s): {caption_text}")
                
        return "\n".join(formatted)

    
    def _create_mcq_prompt(self, question: str, choices: List[str], captions: str) -> str:
        """Create a well-structured prompt for MCQ answering with chain-of-thought"""
        
        choices_formatted = "\n".join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])
        
        prompt = f"""Based on the following video frame descriptions, answer the multiple choice question.

VIDEO FRAME DESCRIPTIONS:
{captions}

QUESTION: {question}

ANSWER CHOICES:
{choices_formatted}

Instructions: For the following, please think out loud, write down all your reasoning, and add it to a "reasoning" section numbered 1 to 4.
1. First, carefully analyze the video frame descriptions and identify any spatial information that is relevant to the question, and think out loud.
3. Consider each answer choice, and evaluate it against the evidence from the frames out loud.
4. Choose the answer that best matches what is shown in the frames, and justify your answer out loud.
5. Finally, please present your answer in the format of "The correct answer is: [answer]" """

        return prompt
    
    def get_key_frames(self, captions: List[Dict], question: str, k: int = 5) -> List[Dict]:
        """
        Find the top k most related key frames from captions based on the question
        
        Args:
            captions: List of caption dictionaries with frame info
            question: The question to find relevant frames for
            k: Number of top frames to return
            
        Returns:
            List of k most relevant caption dictionaries
        """
        if not captions:
            return []
            
        # Extract caption text from each frame
        caption_texts = []
        for cap_data in captions:
            caption_text = cap_data.get('captions', '')
            if isinstance(caption_text, dict):
                # Handle case where captions is a dict
                caption_text = str(caption_text)
            caption_texts.append(caption_text)
        
        # Encode question and captions
        question_embedding = self.sentence_model.encode([question])
        caption_embeddings = self.sentence_model.encode(caption_texts)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(question_embedding, caption_embeddings)[0]
        
        # Get top k indices
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # Return top k frames
        key_frames = [captions[i] for i in top_k_indices]
        
        return key_frames

    
    def gen_specific_prompt(self, question: str, choices: List[str]) -> str:
        """
        Generate a specific prompt for recaptioning frames based on the question and choices
        
        Args:
            question: The question to answer
            choices: List of answer choices
            
        Returns:
            Specific prompt for image captioning focused on the question
        """
        choices_text = ", ".join(choices)
        
        prompt = f"""Read this question: "{question}" and choices: {choices_text}.
        Looking at the frame, describe all the objects that appear in both the question and the frame in great detail. 
        If the objects in the question and choices are related to the frame, describe them based only on the frame in great detail. 
        """
        return prompt
    
    def answer_mcq_with_enhanced_workflow(self, 
                                        question: str, 
                                        choices: List[str], 
                                        captions: List[Dict],
                                        k: int = 10) -> Dict[str, Any]:
        """
        1. Use LLM reasoning to select key frames from all captions
        2. Generate specific prompts for recaptioning
        3. Recaption the key frames with specific prompts
        4. Answer the MCQ using the enhanced captions
        
        Args:
            question: The question to answer
            choices: List of answer choices
            captions: List of caption dictionaries with frame info
            k: Number of key frames to use
            
        Returns:
            Dict with predicted answer, confidence, and reasoning
        """
        from b_image_captioner import ImageCaptioner
        from llm_frame_selector import LLMFrameSelector
        
        # Step 1: Use LLM reasoning to select key frames
        print(f"Using LLM to analyze {len(captions)} captions and select key frames...")
        frame_selector = LLMFrameSelector()
        key_frames = frame_selector.select_key_frames(captions, question, choices, max_frames=k)
        print("key frames: ", key_frames)

        key_frames_data = []
        for frame in key_frames:
            key_frames_data.append((frame['timestamp'], frame['frame_path'], Image.open(frame['frame_path'])))
        
        # Step 2: Generate specific prompt for recaptioning
        specific_prompt = self.gen_specific_prompt(question, choices)
        
        # Step 3: Recaption key frames with specific prompt
        print("Generating enhanced captions for selected key frames...")
        captioner = ImageCaptioner()
        enhanced_captions = []
        
        with open("question_set/key_frames.txt", "a") as key_frames_file: 
            key_frames_file.write(f"Key frames for question: {question}\n")
            key_frames_file.write("=" * 60 + "\n\n")
            enhanced_captions = captioner.caption_frames(key_frames_data, specific_prompt, captions_on = False)
            key_frames_file.write(f"Enhanced caption for frames: {enhanced_captions}...")
            
        # Step 4: Answer MCQ with enhanced captions
        print("Generating final answer using enhanced captions...")
        result = self.answer_mcq_with_captions(question, choices, enhanced_captions)
        
        # Clear CUDA memory
        
        return result


def load_video_captions(captions_file: str = "captions/video_captions.json") -> List[Dict]:
    """Load video captions from JSON file"""
    with open(captions_file, 'r') as f:
        return json.load(f)



if __name__ == "__main__":
    pass