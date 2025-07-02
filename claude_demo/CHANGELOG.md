# Video Understanding Framework - Changelog

## Latest Update: Data Directory Migration

### Changes Made

**File Path Updates:**
- **Frame Storage**: Moved from `frames/` → `data/frames/`
- **Caption Storage**: Moved from `video_captions.json` → `data/video_captions.json`  
- **Test Files**: Now saved to `data/test_video.mp4` and `data/uploaded_video.mp4`

**Files Modified:**
1. `video_frame_extractor.py` - Updated default output directory
2. `video_qa_system.py` - Updated default captions file path
3. `image_captioner.py` - Updated default save path for captions
4. `video_understanding_framework.py` - Updated frames and captions paths
5. `test_framework.py` - Updated test video path
6. `gradio_interface.py` - Updated uploaded video path
7. `setup.py` - Added data directory creation
8. `README.md` - Updated file structure documentation

**Benefits:**
- **More Storage Space**: The `data/` directory has significantly more available space
- **Better Organization**: Separates framework code from generated data
- **Scalability**: Can handle larger videos and more extensive caption datasets
- **Cleaner Structure**: Keeps the main directory uncluttered

**Backward Compatibility:**
- All existing functionality remains the same
- Only storage locations have changed
- Setup script automatically creates required directories

### Directory Structure (New)

```
claude_demo/
├── video.mp4                          # Input video
├── requirements.txt                   # Dependencies  
├── [framework files]                  # Python modules
├── data/                             # Data directory (more space)
│   ├── frames/                       # Extracted frames
│   ├── video_captions.json          # Generated captions
│   ├── test_video.mp4               # Test video segment
│   └── uploaded_video.mp4           # Web interface uploads
├── todo_list.md                     # Progress tracking
├── mistakes_and_bugs.md             # Issue tracking
└── README.md                        # Documentation
```

### Migration Notes

**For New Users:**
- Run `python setup.py` to create the directory structure automatically
- No manual migration needed

**For Existing Users:**
- Old frame and caption files can be moved to the new `data/` directory if desired
- Or simply regenerate by processing videos again

### Testing Verification

✅ All path updates tested and working  
✅ Directory creation verified  
✅ Import statements functional  
✅ Framework components properly configured  

The framework is now optimized for better data storage management while maintaining all existing functionality.