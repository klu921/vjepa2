# LCVR Project - File and Directory Overview

This document provides a comprehensive overview of all files and directories in the LCVR project, explaining what each file does and its purpose in the overall system.

## Project Overview

LCVR is a research project that combines:
- **V-JEPA 2**: A video understanding model using Joint Embedding Predictive Architecture
- **HourVideo**: A benchmark for 1-hour video-language understanding tasks

## Root Directory Files

### Core Project Files
- **README.md**: Main project documentation with setup instructions and usage examples
- **LICENSE**: MIT license from Meta Platforms
- **APACHE-LICENSE**: Apache 2.0 license file
- **setup.py**: Python package setup script for installing LCVR as a package
- **requirements.txt**: Python dependencies including PyTorch, transformers, and video processing libraries
- **requirements-test.txt**: Test-specific dependencies
- **pyproject.toml**: Configuration for code formatting (Black, isort)

### Configuration and Data Files
- **hubconf.py**: PyTorch Hub integration for easy model loading
- **ssv2_classes.json**: Something-Something V2 dataset class labels (174 action classes)
- **sample_video.mp4**: Demo video file for testing the models
- **miniconda.sh**: Script for installing Miniconda environment

### Project Governance
- **CODE_OF_CONDUCT.md**: Community guidelines and standards
- **CONTRIBUTING.md**: Guidelines for contributing to the project
- **CHANGELOG.md**: Project version history and changes

## Major Directories

### `/HourVideo/` - Submodule
Git submodule containing the HourVideo benchmark for long-form video understanding.

#### Core Module (`/HourVideo/hourvideo/`)
- **__init__.py**: Package initialization
- **form_world_state_history.py**: Creates world state representations from video sequences
- **gemini_qa.py**: Google Gemini integration for video question answering
- **gemini_utils.py**: Utility functions for Gemini API interactions
- **gpt4_captioner.py**: GPT-4 based video captioning functionality
- **gpt4_qa.py**: GPT-4 integration for video question answering
- **gpt4_utils.py**: Utility functions for GPT-4 API interactions
- **hv_utils.py**: General HourVideo utilities
- **llm_utils.py**: Common LLM interaction utilities

#### Demo and Configuration
- **demo_notebooks/**: Jupyter notebooks demonstrating GPT-4 and Gemini usage
  - `gemini-1.5.ipynb`: Gemini 1.5 video analysis demo
  - `gpt-4.ipynb`: GPT-4 video analysis demo
- **requirements_gemini.txt**: Gemini-specific dependencies
- **requirements_gpt4.txt**: GPT-4 specific dependencies
- **env.json**: Environment configuration file

### `/src/` - Core Implementation
*Note: This directory contains the main V-JEPA 2 implementation but wasn't fully visible in the listing*

### `/app/` - Training Applications
Training orchestration and main entry points.

- **main.py**: Local training entry point
- **main_distributed.py**: Distributed training across multiple GPUs/nodes
- **scaffold.py**: Training framework and utilities

#### V-JEPA Training (`/app/vjepa/`)
- **train.py**: Core V-JEPA training loop
- **transforms.py**: Video augmentation and preprocessing transforms
- **utils.py**: Training utilities and helper functions

#### Action-Conditioned Training (`/app/vjepa_droid/`)
- **droid.py**: DROID robotics dataset integration
- **train.py**: Action-conditioned training loop for robotics
- **transforms.py**: Robotics-specific data transformations
- **utils.py**: Robotics training utilities

### `/evals/` - Evaluation Framework
Comprehensive evaluation suite for various video understanding tasks.

- **main.py**: Local evaluation entry point
- **main_distributed.py**: Distributed evaluation
- **scaffold.py**: Evaluation framework

#### Action Anticipation (`/evals/action_anticipation_frozen/`)
Epic-Kitchens action anticipation evaluation:
- **dataloader.py**: Epic-Kitchens dataset loader
- **epickitchens.py**: Epic-Kitchens specific utilities
- **eval.py**: Action anticipation evaluation logic
- **losses.py**: Loss functions for action anticipation
- **metrics.py**: Evaluation metrics
- **models.py**: Model architectures for action anticipation
- **utils.py**: Evaluation utilities

#### Video Classification (`/evals/video_classification_frozen/`)
- **eval.py**: Video classification evaluation (Something-Something V2, Diving48)
- **models.py**: Classification model architectures
- **utils.py**: Classification utilities

#### Image Classification (`/evals/image_classification_frozen/`)
- **eval.py**: Image classification evaluation
- **models.py**: Image classification models

#### Hub Integration (`/evals/hub/`)
- **__init__.py**: Package initialization
- **preprocessor.py**: Data preprocessing for evaluations

### `/configs/` - Configuration Files
YAML configuration files for training and evaluation:
- **eval/**: Evaluation configurations for different benchmarks
- **inference/**: Inference configurations for pretrained models  
- **train/**: Training configurations for different model sizes and datasets

### `/notebooks/` - Demos and Examples
Interactive demonstrations and example scripts:

- **vjepa2_demo.ipynb**: Main Jupyter notebook demo of V-JEPA 2
- **vjepa2_demo.py**: Python script version of the demo
- **energy_landscape_example.ipynb**: Demonstrates action-conditioned model energy landscapes
- **get_weights.py**: Script to download pretrained model weights
- **franka_example_traj.npz**: Example trajectory data for robotics demos

#### Utilities (`/notebooks/utils/`)
- **mpc_utils.py**: Model Predictive Control utilities
- **world_model_wrapper.py**: Wrapper for world model inference 

### `/semantic_memory_baseline/` - Baseline Implementation
Simple baseline for semantic memory tasks:

- **main.py**: Basic script loading HuggingFace model for comparison
- **video.mp4**: Source video file for baseline testing
- **frames/**: Contains 809 sequential video frames (frame_0001.jpg to frame_0809.jpg) extracted from the video

### `/data/` - Model Storage
- **LCVR_weights/**: Directory for storing pretrained model weights and checkpoints

### `/assets/` - Project Media
Visual assets and documentation images:
- **flowchart.png**: Project architecture flowchart
- **vjepa2-abstract-new.png**: V-JEPA 2 model abstract visualization
- **vjepa2-ac-abstract-new.png**: Action-conditioned V-JEPA abstract visualization

### `/documentation/` - Project Documentation
- **ex_tut.mkd**: Example tutorial documentation
- **vjepa2_demo_tutorial.md**: Detailed tutorial for V-JEPA 2 demo
- **file_directory_overview.md**: This file - comprehensive directory overview

### `/tests/` - Testing
- **__init__.py**: Test package initialization
- Additional test files (basic test structure)

### Build and Distribution
- **build/**: Build artifacts and temporary files
- **vjepa2.egg-info/**: Python package metadata
  - **PKG-INFO**: Package information
  - **SOURCES.txt**: Source file listing
  - **dependency_links.txt**: Dependency links
  - **requires.txt**: Package requirements
  - **top_level.txt**: Top-level modules
- **frames/**: Empty directory for frame extraction (used by processing scripts)

## Key Entry Points

### Training
```bash
# Local training
python -m app.main --fname configs/train/vitl16/pretrain-256px-16f.yaml

# Distributed training  
python -m app.main_distributed
```

### Evaluation
```bash
# Local evaluation
python -m evals.main --fname configs/eval/vitl/ssv2.yaml

# Distributed evaluation
python -m evals.main_distributed
```

### Demo Usage
```bash
# Run demo script
python -m notebooks.vjepa2_demo

# Or use Jupyter notebooks in notebooks/ directory
```

### Model Loading (PyTorch Hub)
```python
import torch
model = torch.hub.load('facebookresearch/vjepa', 'vjepa_vitl16')
```

## File Type Summary

- **Python files (.py)**: Core implementation files
- **Jupyter notebooks (.ipynb)**: Interactive demos and examples
- **YAML files**: Configuration files for training/evaluation  
- **JSON files**: Data files (class labels, environment config)
- **Image files (.jpg, .png)**: Video frames and project assets
- **Video files (.mp4)**: Demo and test videos
- **Text files (.txt, .md)**: Documentation and requirements
- **Shell scripts (.sh)**: Installation and setup scripts

This project represents a comprehensive research codebase for video understanding with both academic benchmarks and practical robotics applications, featuring state-of-the-art self-supervised learning techniques and extensive evaluation frameworks.