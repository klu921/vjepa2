#!/usr/bin/env python3
"""
Interactive LLM-VLM Pipeline for MCQ Answering

This system implements a collaborative pipeline where:
1. LLM Coordinator receives MCQ questions and coordinates the entire process
2. LLM Frame Selector selects relevant frames based on LLM questions
3. VLM analyzes selected frames and answers LLM questions
4. The process loops until the LLM is confident in its answer

All interactions are logged for transparency.
"""

import json
import time
from typing import List, Dict, Any, Optional
from together import Together
from datetime import datetime
import os
from prompts import get_initial_prompt, get_frame_selector_prompt, get_vlm_prompt

class InteractivePipeline:
    def __init__(self, 
                 llm_model: str = "deepseek-ai/DeepSeek-V3",
                 frame_selector_model: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", 
                 vlm_model: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                 captions_file: str = "video_captions.json",
                 log_file: str = "pipeline_log.txt"):
        """
        Initialize the interactive pipeline system
        
        Args:
            llm_model: Main LLM coordinator model
            frame_selector_model: LLM model for frame selection
            vlm_model: Vision-Language Model for image analysis
            captions_file: Path to video captions file
            log_file: Path to log file for all interactions
        """
        self.client = Together()
        self.llm_model = llm_model
        self.frame_selector_model = frame_selector_model
        self.vlm_model = vlm_model
        self.captions_file = captions_file
        self.log_file = log_file
        
        # Load video captions
        self.captions = self._load_captions()
        
        # Initialize logging
        self._setup_logging()
        
        # Conversation history for context
        self.conversation_history = []
        
        # Configuration
        self.max_iterations = 10
        self.max_retries = 6
        self.retry_delay = 10
        
    def _load_captions(self) -> List[Dict]:
        """Load video captions from JSON file"""
        try:
            with open(self.captions_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Captions file {self.captions_file} not found")
            return []
    

    def _setup_logging(self):
        """Setup logging system"""
        with open(self.log_file, 'w') as f:
            f.write(f"Interactive Pipeline Log - Started at {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
    

    def _log_interaction(self, component: str, interaction_type: str, content: str):
        """Log all interactions between components"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {component} - {interaction_type}:\n{content}\n\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
            f.flush()
        
        print(f"[{component}] {interaction_type}")
    

    def _make_api_call(self, model: str, messages: List[Dict], content_type: str = "text") -> str:
        """Make API call with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if content_type == "text":
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=False
                    )
                else:
                    # For multimodal calls
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=False
                    )
                
                return response.choices[0].message.content
                
            except Exception as e:
                if "rate" in str(e).lower() and attempt < self.max_retries - 1:
                    print(f"Rate limited on attempt {attempt + 1}. Waiting {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise e
        return ""
    
    def llm_coordinator(self, question: str, choices: List[str]) -> Dict[str, Any]:
        """
        Main LLM coordinator that orchestrates the entire process
        
        Args:
            question: MCQ question to answer
            choices: List of answer choices
            
        Returns:
            Dict containing final answer and reasoning
        """
        self._log_interaction("LLM_COORDINATOR", "START", f"Question: {question}\nChoices: {choices}")
        
        # Initialize conversation history
        self.conversation_history = []
        self.selected_frames_cache = {}  # Track selected frames by query
        
        # Initial prompt to LLM coordinator - emphasizes iterative exploration
        initial_prompt = get_initial_prompt(question, choices)
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            # Build conversation context
            if iteration == 1:
                messages = [{"role": "user", "content": initial_prompt}]
            else:
                # Build full conversation history
                messages = [{"role": "user", "content": initial_prompt}]
                for entry in self.conversation_history:
                    messages.append({"role": "assistant", "content": entry["llm_response"]})
                    messages.append({"role": "user", "content": f"""Response: {entry['system_response']}\n\nWhat would you like to do next? You can choose ONE action: FRAME_SELECTOR, VLM, CONTINUE, or FINAL_ANSWER, and format your requests as EXACTLY ONE OF THE FOLLOWING: 
                    
                    FRAME_SELECTOR: [Your specific question/request to find relevant frames] 
                    VLM: [Your specific question about the frames - be detailed about what you want to know] 
                    CONTINUE: [Explanation of what more information you need and your next question] 
                    FINAL_ANSWER: Your final answer here if you have enough information.
                    
                    Only choose FINAL_ANSWER if you are confident you have enough information to answer the question."""})
            
            llm_response = self._make_api_call(self.llm_model, messages)

            self._log_interaction("LLM_COORDINATOR", f"ITERATION_{iteration}", llm_response)
            
            # Check if LLM provided final answer
            if "FINAL_ANSWER:" in llm_response:
                final_answer = llm_response.split("FINAL_ANSWER:")[1].strip()
                self._log_interaction("LLM_COORDINATOR", "FINAL_ANSWER", final_answer)
                return {
                    "answer": final_answer,
                    "reasoning": llm_response,
                    "iterations": iteration,
                    "conversation_history": self.conversation_history
                }
            
            # Process LLM requests
            system_response = ""
            
            if "FRAME_SELECTOR:" in llm_response:
                frame_query = llm_response.split("FRAME_SELECTOR:")[1].split("VLM:")[0].split("CONTINUE:")[0].strip()
                selected_frames = self.frame_selector(frame_query, question, choices)
                
                # Cache the selected frames for this query
                query_id = f"query_{iteration}"
                self.selected_frames_cache[query_id] = selected_frames
                
                frame_summary = []
                for i, frame in enumerate(selected_frames):
                    frame_summary.append(f"Frame {i+1}: {frame['timestamp']:.1f}s - {frame['captions'][:100]}...")
                
                system_response = f"FRAME_SELECTOR found {len(selected_frames)} relevant frames:\n" + "\n".join(frame_summary)
                
            elif "VLM:" in llm_response:
                vlm_query = llm_response.split("VLM:")[1].split("CONTINUE:")[0].strip()
                
                # Get the most recently selected frames
                frames_to_analyze = None
                if self.selected_frames_cache:
                    # Use the most recent frame selection
                    latest_query = max(self.selected_frames_cache.keys())
                    frames_to_analyze = self.selected_frames_cache[latest_query]
                else:
                    # Fallback to first few frames
                    frames_to_analyze = self.captions[:3]
                
                vlm_response = self.vlm_analyzer(vlm_query, frames_to_analyze)
                system_response = f"VLM ANALYSIS:\n{vlm_response}"
                
            elif "CONTINUE:" in llm_response:
                continue_reasoning = llm_response.split("CONTINUE:")[1].strip()
                system_response = f"Understood. You want to continue gathering information: {continue_reasoning}\nWhat specific question would you like to ask next?"
                
            else:
                system_response = "Please specify EXACTLY ONE next action:\n- FRAME_SELECTOR: [question] to find relevant frames\n- VLM: [question] to analyze frames\n- CONTINUE: [reasoning] to explain what more you need\n- FINAL_ANSWER: [answer] when you're confident."
            
            self._log_interaction("SYSTEM", "RESPONSE", system_response)
            
            # Add to conversation history
            self.conversation_history.append({
                "iteration": iteration,
                "llm_response": llm_response,
                "system_response": system_response
            })
        
        # If max iterations reached, ask LLM to make best guess
        final_prompt = f"""You've reached the maximum number of iterations ({self.max_iterations}). Based on all the information you've gathered, please provide your best answer to the question:

QUESTION: {question}
CHOICES: {chr(10).join([f"{chr(65+i)}. {choice}" for i, choice in enumerate(choices)])}

Format: FINAL_ANSWER: [Your chosen answer letter and reasoning based on the information gathered]"""
        
        messages = [{"role": "user", "content": final_prompt}]
        final_response = self._make_api_call(self.llm_model, messages)
        
        if "FINAL_ANSWER:" in final_response:
            final_answer = final_response.split("FINAL_ANSWER:")[1].strip()
        else:
            final_answer = "Unable to determine answer - max iterations reached"
        
        return {
            "answer": final_answer,
            "reasoning": final_response,
            "iterations": iteration,
            "conversation_history": self.conversation_history,
            "max_iterations_reached": True
        }
    
    def frame_selector(self, query: str, original_question: str, choices: List[str]) -> List[Dict]:
        """
        Frame selector component using DeepSeek-V3
        
        Args:
            query: Specific query from LLM coordinator
            original_question: Original MCQ question for context
            choices: Answer choices for context
            
        Returns:
            List of selected frame dictionaries
        """
        self._log_interaction("FRAME_SELECTOR", "QUERY", f"Query: {query}\nOriginal Question: {original_question}")
        
        # Format captions for analysis
        captions_text = ""
        for i, cap_data in enumerate(self.captions):
            timestamp = cap_data.get('timestamp', 0)
            caption = cap_data.get('captions', '')
            captions_text += f"Frame {i+1} (at {timestamp:.1f}s):\n{caption}\n\n"
        
        # Create frame selection prompt
        prompt = get_frame_selector_prompt(query, original_question, choices, captions_text)
        
        messages = [{"role": "user", "content": prompt}]
        response = self._make_api_call(self.frame_selector_model, messages)
        
        self._log_interaction("FRAME_SELECTOR", "SELECTION_RESPONSE", response)
        
        # Parse selected frames
        selected_indices = self._parse_frame_selection(response)
        selected_frames = [self.captions[i] for i in selected_indices if i < len(self.captions)]
        
        self._log_interaction("FRAME_SELECTOR", "SELECTED_FRAMES", 
                            f"Selected {len(selected_frames)} frames: {[f['timestamp'] for f in selected_frames]}")
        
        return selected_frames
    
    def vlm_analyzer(self, query: str, frames: List[Dict]) -> str:
        """
        VLM component for analyzing frames using Llama Maverick
        
        Args:
            query: Question/request from LLM coordinator
            frames: List of frame dictionaries to analyze
            
        Returns:
            VLM analysis response
        """
        self._log_interaction("VLM", "QUERY", f"Query: {query}\nFrames: {[f['timestamp'] for f in frames]}")
        
        # Create multimodal prompt that encourages detailed analysis
        prompt = get_vlm_prompt(query) 

        # Prepare multimodal content
        content = [{"type": "text", "text": prompt}]
        
        # Add images to the request
        import base64
        for i, frame in enumerate(frames[:5]):  # Limit to 5 frames to avoid token limits
            frame_path = frame['frame_path']
            try:
                with open(frame_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })
            except FileNotFoundError:
                print(f"Warning: Frame file {frame_path} not found")
                continue
        
        messages = [{"role": "user", "content": content}]
        
        response = self._make_api_call(self.vlm_model, messages, content_type="multimodal")
        
        self._log_interaction("VLM", "ANALYSIS_RESPONSE", response)
        
        return response
    
    def _parse_frame_selection(self, response: str) -> List[int]:
        """Parse frame selection from LLM response"""
        selected_indices = []
        
        # Look for "SELECTED_FRAMES:" section
        if "SELECTED_FRAMES:" in response:
            frame_part = response.split("SELECTED_FRAMES:")[1].split('\n')[0].strip()
            try:
                frame_numbers = [int(x.strip()) for x in frame_part.split(',') if x.strip().isdigit()]
                selected_indices = [max(0, f-1) for f in frame_numbers if 1 <= f <= len(self.captions)]
            except ValueError:
                pass
        
        # Fallback: use first few frames
        if not selected_indices:
            selected_indices = list(range(min(3, len(self.captions))))
        
        return selected_indices  # Limit to 8 frames
    
    def process_mcq(self, question: str, choices: List[str]) -> Dict[str, Any]:
        """
        Process a single MCQ question through the interactive pipeline
        
        Args:
            question: The MCQ question
            choices: List of answer choices
            
        Returns:
            Complete result including answer, reasoning, and logs
        """
        self._log_interaction("PIPELINE", "START", f"Processing MCQ: {question}")
        
        start_time = time.time()
        
        try:
            result = self.llm_coordinator(question, choices)
            
            result.update({
                "question": question,
                "choices": choices,
                "processing_time": time.time() - start_time,
                "log_file": self.log_file
            })
            
            self._log_interaction("PIPELINE", "COMPLETE", f"Final answer: {result['answer']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            self._log_interaction("PIPELINE", "ERROR", error_msg)
            
            return {
                "question": question,
                "choices": choices,
                "answer": "Error processing question",
                "reasoning": error_msg,
                "processing_time": time.time() - start_time,
                "log_file": self.log_file,
                "error": True
            }


def main():
    """Test the interactive pipeline"""
    # Initialize pipeline
    pipeline = InteractivePipeline()
    
    # Test question
    test_question = "What is the person doing in the kitchen?"
    test_choices = [
        "Cooking food on the stove",
        "Washing dishes at the sink", 
        "Opening the refrigerator",
        "Setting the table"
    ]
    
    print("Testing Interactive Pipeline...")
    print(f"Question: {test_question}")
    print(f"Choices: {test_choices}")
    print("\nProcessing...")
    
    # Process the question
    result = pipeline.process_mcq(test_question, test_choices)
    
    print(f"\nResult:")
    print(f"Answer: {result['answer']}")
    print(f"Processing time: {result['processing_time']:.2f} seconds")
    print(f"Iterations: {result.get('iterations', 'N/A')}")
    print(f"Log file: {result['log_file']}")
    
    print("\nCheck the log file for detailed interaction history.")


if __name__ == "__main__":
    main()