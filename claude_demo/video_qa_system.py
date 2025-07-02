import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import faiss
from typing import List, Dict, Any, Tuple
import re

class VideoQASystem:
    def __init__(self, captions_file: str = "data/video_captions.json"):
        """
        Initialize the Video Question Answering System
        """
        self.captions_file = captions_file
        self.captions_data = None
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize QA pipeline for more complex reasoning
        self.qa_pipeline = pipeline("question-answering", 
                                  model="deepset/roberta-base-squad2")
        
        # Storage for embeddings and FAISS index
        self.caption_embeddings = None
        self.faiss_index = None
        self.caption_texts = []
        self.frame_mapping = []
        
        self.load_captions()
        self.build_search_index()
    
    def load_captions(self):
        """Load captions from JSON file"""
        try:
            with open(self.captions_file, 'r') as f:
                self.captions_data = json.load(f)
            print(f"Loaded captions for {len(self.captions_data)} frames")
        except FileNotFoundError:
            print(f"Captions file {self.captions_file} not found")
            self.captions_data = []
    
    def build_search_index(self):
        """Build FAISS search index from captions for semantic search"""
        if not self.captions_data:
            return
        
        all_texts = []
        frame_mappings = []
        
        for frame_idx, frame_data in enumerate(self.captions_data):
            timestamp = frame_data['timestamp']
            captions = frame_data['captions']
            
            # Combine all captions for this frame
            combined_caption = " ".join([
                captions.get('general', ''),
                captions.get('detailed_1', ''),
                captions.get('detailed_2', ''),
                captions.get('detailed_3', ''),
                captions.get('detailed_4', ''),
                captions.get('detailed_5', '')
            ])
            
            all_texts.append(combined_caption)
            frame_mappings.append({
                'frame_idx': frame_idx,
                'timestamp': timestamp,
                'captions': captions
            })
        
        # Generate embeddings
        self.caption_embeddings = self.sentence_model.encode(all_texts)
        
        # Build FAISS index
        dimension = self.caption_embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.caption_embeddings)
        self.faiss_index.add(self.caption_embeddings)
        
        self.caption_texts = all_texts
        self.frame_mapping = frame_mappings
        
        print(f"Built search index with {len(all_texts)} frame captions")
    
    def search_relevant_frames(self, question: str, top_k: int = 5) -> List[Dict]:
        """
        Search for frames most relevant to the question
        """
        if not self.faiss_index:
            return []
        
        # Encode question
        question_embedding = self.sentence_model.encode([question])
        faiss.normalize_L2(question_embedding)
        
        # Search
        scores, indices = self.faiss_index.search(question_embedding, top_k)
        
        relevant_frames = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.frame_mapping):
                frame_info = self.frame_mapping[idx].copy()
                frame_info['relevance_score'] = float(score)
                relevant_frames.append(frame_info)
        
        return relevant_frames
    
    def answer_question(self, question: str, use_context: bool = True) -> Dict[str, Any]:
        """
        Answer a question about the video using the captions
        """
        if not self.captions_data:
            return {"error": "No captions data available"}
        
        # Find relevant frames
        relevant_frames = self.search_relevant_frames(question, top_k=3)
        
        if not relevant_frames:
            return {"error": "No relevant frames found"}
        
        # Combine context from relevant frames
        context_parts = []
        frame_references = []
        
        for frame in relevant_frames:
            timestamp = frame['timestamp']
            captions = frame['captions']
            
            # Create comprehensive context
            frame_context = f"At {timestamp:.1f} seconds: "
            frame_context += captions.get('general', '') + " "
            frame_context += captions.get('detailed_1', '') + " "
            frame_context += captions.get('detailed_2', '') + " "
            
            context_parts.append(frame_context)
            frame_references.append({
                'timestamp': timestamp,
                'relevance_score': frame['relevance_score']
            })
        
        combined_context = " ".join(context_parts)
        
        # Use QA pipeline to generate answer
        try:
            result = self.qa_pipeline(question=question, context=combined_context)
            
            return {
                'question': question,
                'answer': result['answer'],
                'confidence': result['score'],
                'relevant_frames': frame_references,
                'context_used': combined_context[:500] + "..." if len(combined_context) > 500 else combined_context
            }
        except Exception as e:
            return {
                'question': question,
                'answer': f"Could not generate answer: {str(e)}",
                'confidence': 0.0,
                'relevant_frames': frame_references
            }
    
    def answer_multiple_choice(self, question: str, choices: List[str]) -> Dict[str, Any]:
        """
        Answer a multiple choice question
        """
        # Get basic answer first
        base_answer = self.answer_question(question)
        
        if 'error' in base_answer:
            return base_answer
        
        # Find best matching choice
        answer_text = base_answer['answer'].lower()
        relevant_context = base_answer['context_used'].lower()
        
        choice_scores = []
        for i, choice in enumerate(choices):
            choice_lower = choice.lower()
            
            # Score based on answer text similarity
            answer_score = 1.0 if choice_lower in answer_text else 0.0
            
            # Score based on context similarity
            context_score = 0.5 if any(word in relevant_context for word in choice_lower.split()) else 0.0
            
            # Use sentence transformer for semantic similarity
            choice_embedding = self.sentence_model.encode([choice])
            answer_embedding = self.sentence_model.encode([base_answer['answer']])
            
            semantic_score = float(np.dot(choice_embedding[0], answer_embedding[0]) / 
                                 (np.linalg.norm(choice_embedding[0]) * np.linalg.norm(answer_embedding[0])))
            
            total_score = answer_score + context_score + semantic_score
            choice_scores.append(total_score)
        
        best_choice_idx = np.argmax(choice_scores)
        
        return {
            'question': question,
            'choices': choices,
            'selected_choice': choices[best_choice_idx],
            'choice_index': best_choice_idx,
            'confidence': choice_scores[best_choice_idx],
            'reasoning': base_answer['answer'],
            'relevant_frames': base_answer['relevant_frames']
        }
    
    def get_timeline_summary(self) -> List[Dict]:
        """
        Get a summary of what happens throughout the video
        """
        if not self.captions_data:
            return []
        
        timeline = []
        for frame_data in self.captions_data:
            timeline.append({
                'timestamp': frame_data['timestamp'],
                'summary': frame_data['captions'].get('general', 'No caption available')
            })
        
        return timeline
    
    def evaluate_on_dataset(self, dataset_file: str = "HourVideo_Dataset.csv") -> Dict[str, Any]:
        """
        Evaluate the QA system on questions from the dataset CSV (every 10th question)
        """
        try:
            df = pd.read_csv(dataset_file)
        except FileNotFoundError:
            return {"error": f"Dataset file {dataset_file} not found"}
        
        # Sample every 10th question
        df = df.iloc[::10]
        
        results = []
        correct_answers = 0
        total_questions = len(df)
        
        for idx, row in df.iterrows():
            question = row['question']
            task_type = row['task']
            
            # Get answer choices
            choices = [
                row['answer_1'],
                row['answer_2'], 
                row['answer_3'],
                row['answer_4'],
                row['answer_5']
            ]
            
            # Remove any NaN choices
            choices = [choice for choice in choices if pd.notna(choice)]
            
            # Get system answer
            system_result = self.answer_multiple_choice(question, choices)
            
            if 'error' not in system_result:
                predicted_choice = system_result['selected_choice']
                predicted_index = system_result['choice_index']
                
                # The correct answer is always answer_1 (option A)
                correct_answer = row['answer_1']
                is_correct = predicted_choice == correct_answer
                
                if is_correct:
                    correct_answers += 1
                
                results.append({
                    'question_id': idx,
                    'question': question,
                    'task_type': task_type,
                    'predicted_answer': predicted_choice,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct,
                    'confidence': system_result['confidence'],
                    'predicted_index': predicted_index
                })
            else:
                results.append({
                    'question_id': idx,
                    'question': question,
                    'task_type': task_type,
                    'error': system_result['error'],
                    'is_correct': False
                })
        
        accuracy = correct_answers / total_questions if total_questions > 0 else 0
        
        # Calculate accuracy by task type
        task_accuracies = {}
        for task_type in df['task'].unique():
            task_results = [r for r in results if r.get('task_type') == task_type]
            task_correct = sum(1 for r in task_results if r.get('is_correct', False))
            task_total = len(task_results)
            task_accuracies[task_type] = task_correct / task_total if task_total > 0 else 0
        
        return {
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'overall_accuracy': accuracy,
            'task_accuracies': task_accuracies,
            'detailed_results': results
        }

if __name__ == "__main__":
    # Test the QA system
    print("Video QA System initialized")
    
    # Example usage (would be used after captions are generated)
    qa = VideoQASystem()
    
    # Run evaluation on spatial reasoning dataset
    print("Running evaluation on spatial reasoning tasks...")
    eval_results = qa.evaluate_on_dataset("spatial_reasoning_dataset.csv")
    
    if 'error' not in eval_results:
        print(f"Overall Accuracy: {eval_results['overall_accuracy']:.2%}")
        print("\nAccuracy by task type:")
        for task, acc in eval_results['task_accuracies'].items():
            print(f"  {task}: {acc:.2%}")
    else:
        print(f"Error: {eval_results['error']}")