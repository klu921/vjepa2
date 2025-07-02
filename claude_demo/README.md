# Video Understanding Framework

A comprehensive multimodal ML framework that processes videos by extracting frames, generating detailed captions, and enabling question-answering about video content.

## Features

- **Frame Extraction**: Extracts frames from videos at specified intervals (default: every 3 seconds)
- **Detailed Captioning**: Uses state-of-the-art HuggingFace models to generate comprehensive captions for each frame
- **Semantic Search**: Builds searchable index of captions using sentence transformers and FAISS
- **Question Answering**: Answers both open-ended and multiple choice questions about video content
- **Interactive Interfaces**: Command-line and web-based interfaces for easy interaction

## Installation

1. Install required dependencies:



```sh
pip install -r requirements.txt
```

2. Ensure you have a video file named `video.mp4` in the project directory

## Usage

### Command Line Interface

Run the main framework:

```sh
python video_understanding_framework.py
```

This will:
1. Extract frames from `video.mp4` every 3 seconds
2. Generate detailed captions for each frame
3. Build a searchable index
4. Enter interactive Q&A mode

### Web Interface

Launch the Gradio web interface:

```sh
python gradio_interface.py
```

Then open your browser to interact with the framework through a user-friendly web interface.

### Programmatic Usage

```python
from video_understanding_framework import VideoUnderstandingFramework

# Initialize and process video
framework = VideoUnderstandingFramework("your_video.mp4")
framework.process_video(interval_seconds=3)

# Ask questions
result = framework.ask_question("What happens in the video?")
print(result['answer'])

# Multiple choice questions
choices = ["Cooking", "Cleaning", "Exercise"]
result = framework.ask_multiple_choice("What activity is happening?", choices)
print(result['selected_choice'])
```

## Architecture

### Components

1. **VideoFrameExtractor** (`video_frame_extractor.py`)
   - Extracts frames at specified intervals
   - Saves frames as high-quality JPEG images
   - Provides video metadata

2. **ImageCaptioner** (`image_captioner.py`)
   - Uses BLIP model for detailed image captioning
   - Generates multiple captions with different prompts for comprehensive understanding
   - Supports alternative models for enhanced detail

3. **VideoQASystem** (`video_qa_system.py`)
   - Builds semantic search index using sentence transformers
   - Uses FAISS for efficient similarity search
   - Employs RoBERTa-based QA model for answer generation

4. **VideoUnderstandingFramework** (`video_understanding_framework.py`)
   - Main orchestrator that combines all components
   - Provides unified interface for video processing and querying

### Data Flow

1. **Video Processing Phase** (Offline, one-time):
   ```
   Video → Frame Extraction → Image Captioning → Caption Storage → Index Building
   ```

2. **Query Phase** (Real-time):
   ```
   Question → Semantic Search → Relevant Frames → Context Assembly → Answer Generation
   ```

## Models Used

- **Image Captioning**: Salesforce/blip-image-captioning-large
- **Semantic Search**: all-MiniLM-L6-v2 (Sentence Transformers)
- **Question Answering**: deepset/roberta-base-squad2
- **Alternative Captioning**: microsoft/git-large-coco

## File Structure

```
claude_demo/
├── video.mp4                          # Input video
├── requirements.txt                   # Dependencies
├── video_understanding_framework.py   # Main framework
├── video_frame_extractor.py          # Frame extraction
├── image_captioner.py                # Image captioning
├── video_qa_system.py                # Q&A system
├── gradio_interface.py               # Web interface
├── data/                             # Data directory (more space)
│   ├── frames/                       # Extracted frames (auto-created)
│   ├── video_captions.json          # Generated captions
│   ├── test_video.mp4               # Test video segment
│   └── uploaded_video.mp4           # Web interface uploads
├── todo_list.md                     # Progress tracking
├── mistakes_and_bugs.md             # Issue tracking
└── README.md                        # This file
```

## Example Questions

The system can handle various types of questions:

### Open-ended Questions
- "What happens in the video?"
- "Why did the camera wearer use the red towel?"
- "What objects can you see in the kitchen?"
- "Describe the person's actions at 30 seconds"

### Multiple Choice Questions
- "What color is the towel? A) Red B) Blue C) Green D) Yellow"
- "What room is this? A) Kitchen B) Bathroom C) Living room D) Bedroom"
- "What activity is happening? A) Cooking B) Cleaning C) Exercise D) Reading"

## Performance Considerations

- **Memory Usage**: Large videos may require significant RAM for frame processing
- **GPU Acceleration**: CUDA-enabled GPU recommended for faster model inference
- **Processing Time**: ~1-2 minutes per minute of video content on modern hardware
- **Storage**: Extracted frames and captions require additional disk space

## Troubleshooting

Common issues and solutions are tracked in `mistakes_and_bugs.md`.

## Limitations

- Currently supports common video formats (MP4, AVI, MOV)
- Caption quality depends on visual clarity of frames
- Best results with videos containing clear, well-lit scenes
- Processing time scales linearly with video length

## Future Enhancements

- Support for audio analysis and speech-to-text
- Real-time video streaming capabilities
- Multi-language caption generation
- Object tracking across frames
- Scene change detection for smarter frame selection