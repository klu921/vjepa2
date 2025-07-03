#!/usr/bin/env python3
"""
Setup script for Video Understanding Framework
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False

def check_video_file():
    """Check if video file exists"""
    if os.path.exists("video.mp4"):
        print("✓ video.mp4 found")
        return True
    else:
        print("✗ video.mp4 not found - please ensure your video file is named 'video.mp4'")
        return False

def create_directories():
    """Create necessary directories"""
    dirs = ["data", "data/frames"]
    
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✓ Created directory: {dir_name}")
        else:
            print(f"✓ Directory exists: {dir_name}")

def main():
    """Main setup function"""
    print("=== Video Understanding Framework Setup ===\n")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 or higher is required")
        return False
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Create directories
    create_directories()
    
    # Check video file
    video_exists = check_video_file()
    
    print("\n=== Setup Complete ===")
    
    if video_exists:
        print("\nYou can now run:")
        print("1. python video_understanding_framework.py  # Command line interface")
        print("2. python gradio_interface.py              # Web interface")
        print("3. python test_framework.py                # Test with short segment")
    else:
        print("\nPlease add your video file as 'video.mp4' then run the framework")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)