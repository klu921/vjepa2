# Mistakes and Bugs Log

## Potential Issues to Watch For
- Memory usage when loading large video files (60+ min videos may need chunking)
- GPU memory management with multiple HuggingFace models
- Frame extraction accuracy at exactly 3-second intervals
- Caption quality and detail level for complex scenes
- Video format compatibility (tested with MP4, may need codec adjustments)

## Implementation Notes
- Used BLIP for image captioning (good balance of speed vs. quality)
- FAISS with inner product similarity for semantic search
- RoBERTa-based QA model for answer generation
- Multiple caption prompts per frame for comprehensive understanding

## Best Practices Implemented
- Modular architecture for easy component swapping
- JSON storage for offline caption querying
- Semantic search with relevance scoring
- Both CLI and web interfaces for accessibility
- Test framework for validation

## Resolved Issues
- Large video handling: Created test framework with shorter segments
- Setup complexity: Added setup.py for one-command installation
- Interface accessibility: Provided both CLI and web GUI options

## Performance Optimizations
- Frame extraction every 3-5 seconds (configurable)
- Batch processing for captions
- FAISS indexing for fast similarity search
- Normalized embeddings for consistent scoring
- Data storage moved to `data/` directory for better space management

## Recent Updates
- Updated all file paths to use `data/` directory structure
- Frame storage: `data/frames/` instead of `frames/`
- Caption storage: `data/video_captions.json`
- Test files: `data/test_video.mp4`, `data/uploaded_video.mp4`
- Automatic directory creation in setup script

## Current Issues Found (2025-07-07)
- **Caption Quality Issue**: Batch captions (10 images) are much shorter/less detailed than existing single-image captions
- **Directory Structure**: Code uses 'frames/' and 'captions/' but docs specify 'data/frames/' and 'data/'
- **Rate Limiting**: Successfully bypassed with batch processing (10 images per API call)
- **API Usage**: Together AI model `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` has 0.6 queries/minute limit