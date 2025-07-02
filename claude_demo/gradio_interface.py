#!/usr/bin/env python3
"""
Gradio Web Interface for Video Understanding Framework
"""

import gradio as gr
import os
import json
from video_understanding_framework import VideoUnderstandingFramework
from typing import List, Tuple, Optional

class VideoQAInterface:
    def __init__(self):
        self.framework = None
        self.processed = False
        
    def process_video(self, video_file) -> Tuple[str, str]:
        """
        Process uploaded video file
        """
        if video_file is None:
            return "Please upload a video file first.", ""
        
        try:
            # Save uploaded file
            video_path = "data/uploaded_video.mp4"
            with open(video_path, "wb") as f:
                f.write(video_file)
            
            # Initialize framework
            self.framework = VideoUnderstandingFramework(video_path)
            
            # Process video
            success = self.framework.process_video(interval_seconds=3)
            
            if success:
                self.processed = True
                
                # Get timeline for display
                timeline = self.framework.get_timeline()
                timeline_text = "Video Timeline:\n"
                for item in timeline:
                    timeline_text += f"{item['timestamp']:.1f}s: {item['summary']}\n"
                
                return "Video processed successfully! You can now ask questions.", timeline_text
            else:
                return "Failed to process video. Please check the file format.", ""
                
        except Exception as e:
            return f"Error processing video: {str(e)}", ""
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question about the processed video
        """
        if not self.processed or not self.framework:
            return "Please process a video first before asking questions."
        
        if not question.strip():
            return "Please enter a question."
        
        try:
            result = self.framework.ask_question(question)
            
            if 'error' in result:
                return f"Error: {result['error']}"
            
            response = f"Answer: {result['answer']}\n"
            response += f"Confidence: {result['confidence']:.2f}\n"
            
            if result['relevant_frames']:
                timestamps = [f"{f['timestamp']:.1f}s" for f in result['relevant_frames']]
                response += f"Relevant timestamps: {', '.join(timestamps)}"
            
            return response
            
        except Exception as e:
            return f"Error answering question: {str(e)}"
    
    def answer_multiple_choice(self, question: str, choice_a: str, choice_b: str, 
                             choice_c: str = "", choice_d: str = "", choice_e: str = "", choice_f: str = "") -> str:
        """
        Answer a multiple choice question
        """
        if not self.processed or not self.framework:
            return "Please process a video first before asking questions."
        
        if not question.strip() or not choice_a.strip() or not choice_b.strip():
            return "Please provide a question and at least two choices."
        
        # Build choices list
        choices = [choice_a, choice_b]
        if choice_c.strip():
            choices.append(choice_c)
        if choice_d.strip():
            choices.append(choice_d)
        if choice_e.strip():
            choices.append(choice_e)

        
        try:
            result = self.framework.ask_multiple_choice(question, choices)
            
            if 'error' in result:
                return f"Error: {result['error']}"
            
            response = f"Selected Answer: {result['selected_choice']}\n"
            response += f"Reasoning: {result['reasoning']}\n"
            response += f"Confidence: {result['confidence']:.2f}\n"
            
            if result['relevant_frames']:
                timestamps = [f"{f['timestamp']:.1f}s" for f in result['relevant_frames']]
                response += f"Relevant timestamps: {', '.join(timestamps)}"
            
            return response
            
        except Exception as e:
            return f"Error answering multiple choice: {str(e)}"

def create_interface():
    """
    Create the Gradio interface
    """
    qa_interface = VideoQAInterface()
    
    with gr.Blocks(title="Video Understanding Framework") as demo:
        gr.Markdown("# Video Understanding Framework")
        gr.Markdown("Upload a video, process it, and ask questions about what happens in the video!")
        
        with gr.Tab("Video Processing"):
            video_input = gr.File(label="Upload Video File", file_types=[".mp4", ".avi", ".mov"])
            process_btn = gr.Button("Process Video", variant="primary")
            
            with gr.Row():
                status_output = gr.Textbox(label="Processing Status", lines=2)
                timeline_output = gr.Textbox(label="Video Timeline", lines=10)
            
            process_btn.click(
                qa_interface.process_video,
                inputs=[video_input],
                outputs=[status_output, timeline_output]
            )
        
        with gr.Tab("Question Answering"):
            gr.Markdown("### Ask Questions About the Video")
            
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="e.g., Why did the camera wearer use the red towel?",
                lines=2
            )
            
            ask_btn = gr.Button("Ask Question", variant="primary")
            answer_output = gr.Textbox(label="Answer", lines=5)
            
            ask_btn.click(
                qa_interface.answer_question,
                inputs=[question_input],
                outputs=[answer_output]
            )
        
        with gr.Tab("Multiple Choice"):
            gr.Markdown("### Multiple Choice Questions")
            
            mc_question = gr.Textbox(
                label="Question",
                placeholder="What color was the towel used by the camera wearer?",
                lines=2
            )
            
            with gr.Row():
                choice_a = gr.Textbox(label="Choice A", placeholder="Red")
                choice_b = gr.Textbox(label="Choice B", placeholder="Blue")
            
            with gr.Row():
                choice_c = gr.Textbox(label="Choice C (optional)", placeholder="Green")
                choice_d = gr.Textbox(label="Choice D (optional)", placeholder="Yellow")
            with gr.Row():
                choice_e = gr.Textbox(label="Choice E (optional)", placeholder="Orange")
            
            mc_btn = gr.Button("Answer Multiple Choice", variant="primary")
            mc_output = gr.Textbox(label="Answer", lines=5)
            
            mc_btn.click(
                qa_interface.answer_multiple_choice,
                inputs=[mc_question, choice_a, choice_b, choice_c, choice_d, choice_e],
                outputs=[mc_output]
            )
        
        with gr.Tab("Examples"):
            gr.Markdown("### Example Questions You Can Ask:")
            gr.Markdown("""
            - **General Questions:**
              - What happens in the video?
              - Who is in the video?
              - What objects can you see?
            
            - **Specific Questions:**
              - Why did the person use the red towel?
              - What was the person doing at 30 seconds?
              - Where does this video take place?
            
            - **Multiple Choice Examples:**
              - What color is the towel? A) Red B) Blue C) Green
              - What activity is happening? A) Cooking B) Cleaning C) Exercise
            """)
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True, server_name="0.0.0.0")