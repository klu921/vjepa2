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

class LLMMCQAnswerer:

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.1",):

        # Use exactly 2 GPUs
        if torch.cuda.device_count() >= 2:
            self.use_model_parallel = True
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.use_model_parallel = False

        cache_dir = "data/mistral_7b_instruct_weights"
        os.makedirs(cache_dir, exist_ok=True)
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        if self.use_model_parallel:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                device_map="auto"  # Use only GPU 0 and 1
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.model.to(self.device)
        
        # Initialize sentence transformer for finding key frames
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

        if self.use_model_parallel:
            first_device = next(self.model.parameters()).device
            inputs = self.tokenizer(prompt, return_tensors = "pt").to(first_device)
        else:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=300,  # Increased for chain-of-thought reasoning
                temperature=0.3,  # Lower temperature for more focused answers
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode only the new tokens (remove input prompt)
        input_length = inputs.input_ids.shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        predicted_answer = ""
        try:
            predicted_answer = response.split("The correct answer is: ")[1]
        except IndexError:
            predicted_answer = "No answer found"
            
        # Clear CUDA memory after each question
        torch.cuda.empty_cache()
        
        return {
            "predicted_answer": predicted_answer,
            "full_response": response,
            "reasoning": response
        }
        
    
    def _format_captions(self, captions: List[Dict]) -> str:
        """Format captions into readable text for LLM"""
        formatted = []
        
        for i, cap_data in enumerate(captions):
            timestamp = cap_data.get('timestamp', 0)
            captions_dict = cap_data.get('captions', {})
            #TODO: FINISH THIS UP
            for caption in captions_dict:
                formatted.append(f"Frame {i+1} (at {timestamp:.1f}s): {caption}")
                
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
3. Consider each answer choice, and evaluate it against the evidence from the video out loud.
4. Choose the answer that best matches what is shown in the video, and justify your answer out loud.
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
        If the objects in the question and choices are related to the frame, describe them based only on the frame in great detail. Write a caption that might help answer the question."""
        return prompt
    
    def answer_mcq_with_enhanced_workflow(self, 
                                        question: str, 
                                        choices: List[str], 
                                        captions: List[Dict],
                                        k: int = 3) -> Dict[str, Any]:
        """
        1. Find top k most related key frames
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
        
        # Step 1: Find key frames
        key_frames = self.get_key_frames(captions, question, k)
        
        # Step 2: Generate specific prompt for recaptioning
        specific_prompt = self.gen_specific_prompt(question, choices)
        
        # Step 3: Recaption key frames with specific prompt
        captioner = ImageCaptioner()
        enhanced_captions = []
        
        #TODO: move the pipeline to inside the file-writer, so this actually runs correctly + not rerun.
        with open("key_frames.txt", "w") as key_frames_file:
            key_frames_file.write("Key Frames for Questions: \n")
            key_frames_file.write("=" * 60 + "\n\n") 
            
            for frame_data in key_frames:
                frame_path = frame_data.get('frame_path', '')
                timestamp = frame_data.get('timestamp', 0)
                
                if frame_path and os.path.exists(frame_path):
                    # Generate enhanced caption
                    enhanced_caption = captioner.caption_image(frame_path, specific_prompt)
                    enhanced_captions.append({
                        'timestamp': timestamp,
                        'frame_path': frame_path,
                        'captions': enhanced_caption
                    })
                    key_frames_file.write(f"Frame {timestamp}: {enhanced_caption}\n")
        
        # Step 4: Answer MCQ with enhanced captions
        result = self.answer_mcq_with_captions(question, choices, enhanced_captions)
        
        # Clear CUDA memory
        torch.cuda.empty_cache()
        
        return result


def load_video_captions(captions_file: str = "data/video_captions.json") -> List[Dict]:
    """Load video captions from JSON file"""
    with open(captions_file, 'r') as f:
        return json.load(f)



if __name__ == "__main__":
    # Example usage
    answerer = LLMMCQAnswerer("mistralai/Mistral-7B-Instruct-v0.1")
    
    # Load your video captions
    captions = load_video_captions()
    
    # Example MCQ
    sample_mcq = {
        "question": "What is the person in the video doing?",
        "choices": [
            "Cooking in the kitchen",
            "Eating breakfast at a table", 
            "Reading a book",
            "Watching television"
        ],
        "correct_answer": "B"
    }
    
    result = answerer.answer_mcq_with_captions(
        question=sample_mcq["question"],
        choices=sample_mcq["choices"],
        relevant_captions=captions[:3]  # Use first 3 captions
    )
    
    print("MCQ Result:")
    print(f"Question: {sample_mcq['question']}")
    print(f"Predicted Answer: {result['predicted_answer']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}")