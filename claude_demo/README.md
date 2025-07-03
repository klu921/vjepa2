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

3. **VideoUnderstandingFramework** (`video_understanding_framework.py`)
   - Main orchestrator that combines all components
   - Provides unified interface for video processing and querying

### Data Flow

1. **Video Processing Phase** (Offline, one-time):
   ```
   Video → Frame Extraction → Image Captioning → Caption Storage → Index Building
   ```

## Models Used

- **Image Captioning**: Salesforce/blip-image-captioning-large
- **LLM Caption processing**: microsoft/phi-2

## File Structure

```
claude_demo/
├── video.mp4                          # Input video
├── requirements.txt                   # Dependencies
├── video_understanding_framework.py   # Main framework
├── video_frame_extractor.py          # Frame extraction
├── image_captioner.py                # Image captioning
├── answers.txt                        # Where model outputs answers
├── data/                             # Data directory (more space)
│   ├── frames/                       # Extracted frames (auto-created)
│   ├── video_captions.json          # Generated captions
└── README.md                        # This file
```


## Performance Considerations

- **Memory Usage**: Large videos may require significant RAM for frame processing
- **GPU Acceleration**: CUDA-enabled GPU recommended for faster model inference
- **Processing Time**: ~1-2 minutes per minute of video content on modern hardware
- **Storage**: Extracted frames and captions require additional disk space

## Limitations

- Currently supports common video formats (MP4, AVI, MOV)
- Caption quality depends on visual clarity of frames
- Best results with videos containing clear, well-lit scenes
- Processing time scales linearly with video length