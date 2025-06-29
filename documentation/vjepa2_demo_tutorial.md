# VJEPA2 Demo Tutorial: Line-by-Line Breakdown

This tutorial provides a comprehensive line-by-line breakdown of the `vjepa2_demo.py` file, which demonstrates how to use the VJEPA2 (Video Joint Embedding Predictive Architecture) model for video understanding tasks.

## File Overview
The demo script shows how to:
1. Load pretrained VJEPA2 models (both HuggingFace and PyTorch versions)
2. Process video data
3. Extract video features
4. Perform video classification

## Line-by-Line Breakdown

### Lines 1-5: License Header
```python
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
```
Standard Meta copyright and MIT license header.

### Lines 6-19: Imports
```python
import json
import os
import subprocess

import numpy as np
import torch
import torch.nn.functional as F
from decord import VideoReader
from transformers import AutoModel, AutoVideoProcessor

import src.datasets.utils.video.transforms as video_transforms
import src.datasets.utils.video.volume_transforms as volume_transforms
from src.models.attentive_pooler import AttentiveClassifier
from src.models.vision_transformer import vit_giant_xformers_rope
```
- **Lines 6-8**: Standard library imports for JSON handling, OS operations, and subprocess calls
- **Lines 10-12**: Core ML libraries (NumPy, PyTorch, and functional operations)
- **Line 13**: `decord.VideoReader` for efficient video loading
- **Line 14**: HuggingFace transformers for model and processor loading
- **Lines 16-19**: Local project imports for video transforms, classifier, and vision transformer

### Lines 21-22: Constants
```python
IMAGENET_DEFAULT_MEAN = (0.485, 0.456, 0.406)
IMAGENET_DEFAULT_STD = (0.229, 0.224, 0.225)
```
ImageNet normalization constants used for preprocessing video frames.

### Lines 25-33: VJEPA2 Encoder Weight Loading
```python
def load_pretrained_vjepa_pt_weights(model, pretrained_weights):
    # Load weights of the VJEPA2 encoder
    # The PyTorch state_dict is already preprocessed to have the right key names
    pretrained_dict = torch.load(pretrained_weights, weights_only=True, map_location="cpu")["encoder"]
    pretrained_dict = {k.replace("module.", ""): v for k, v in pretrained_dict.items()}
    pretrained_dict = {k.replace("backbone.", ""): v for k, v in pretrained_dict.items()}
    msg = model.load_state_dict(pretrained_dict, strict=False)
    print("Pretrained weights found at {} and loaded with msg: {}".format(pretrained_weights, msg))
```
- **Line 28**: Loads pretrained weights from file, extracting the "encoder" portion
- **Lines 29-30**: Cleans up key names by removing "module." and "backbone." prefixes
- **Line 31**: Loads the cleaned weights into the model (strict=False allows partial loading)
- **Line 32**: Prints confirmation message

### Lines 35-42: VJEPA2 Classifier Weight Loading
```python
def load_pretrained_vjepa_classifier_weights(model, pretrained_weights):
    # Load weights of the VJEPA2 classifier
    # The PyTorch state_dict is already preprocessed to have the right key names
    pretrained_dict = torch.load(pretrained_weights, weights_only=True, map_location="cpu")["classifiers"][0]
    pretrained_dict = {k.replace("module.", ""): v for k, v in pretrained_dict.items()}
    msg = model.load_state_dict(pretrained_dict, strict=False)
    print("Pretrained weights found at {} and loaded with msg: {}".format(pretrained_weights, msg))
```
Similar to encoder loading but for the classifier component, extracting from "classifiers"[0].

### Lines 44-56: Video Transform Pipeline
```python
def build_pt_video_transform(img_size):
    short_side_size = int(256.0 / 224 * img_size)
    # Eval transform has no random cropping nor flip
    eval_transform = video_transforms.Compose(
        [
            video_transforms.Resize(short_side_size, interpolation="bilinear"),
            video_transforms.CenterCrop(size=(img_size, img_size)),
            volume_transforms.ClipToTensor(),
            video_transforms.Normalize(mean=IMAGENET_DEFAULT_MEAN, std=IMAGENET_DEFAULT_STD),
        ]
    )
    return eval_transform
```
- **Line 45**: Calculates resize dimension maintaining aspect ratio
- **Lines 47-54**: Creates evaluation transform pipeline:
  - Resize to calculated short side
  - Center crop to square image
  - Convert to tensor
  - Normalize with ImageNet statistics

### Lines 58-64: Video Loading
```python
def get_video():
    vr = VideoReader("sample_video.mp4")
    # choosing some frames here, you can define more complex sampling strategy
    frame_idx = np.arange(0, 128, 2)
    video = vr.get_batch(frame_idx).asnumpy()
    return video
```
- **Line 59**: Initialize video reader for sample video
- **Line 61**: Sample every 2nd frame from 0 to 127 (64 frames total)
- **Line 62**: Extract selected frames as numpy array
- Returns video tensor with shape (T, H, W, C)

### Lines 66-79: Forward Pass Function
```python
def forward_vjepa_video(model_hf, model_pt, hf_transform, pt_transform):
    # Run a sample inference with VJEPA
    with torch.inference_mode():
        # Read and pre-process the image
        video = get_video()  # T x H x W x C
        video = torch.from_numpy(video).permute(0, 3, 1, 2)  # T x C x H x W
        x_pt = pt_transform(video).cuda().unsqueeze(0)
        x_hf = hf_transform(video, return_tensors="pt")["pixel_values_videos"].to("cuda")
        # Extract the patch-wise features from the last layer
        out_patch_features_pt = model_pt(x_pt)
        out_patch_features_hf = model_hf.get_vision_features(x_hf)

    return out_patch_features_hf, out_patch_features_pt
```
- **Line 68**: Use inference mode for efficiency (no gradient computation)
- **Line 70**: Load video data
- **Line 71**: Convert to tensor and permute to (T, C, H, W) format
- **Lines 72-73**: Apply transforms for both PyTorch and HuggingFace models
- **Lines 75-76**: Extract features from both model versions
- Returns feature tensors from both models for comparison

### Lines 81-97: Classification Results
```python
def get_vjepa_video_classification_results(classifier, out_patch_features_pt):
    SOMETHING_SOMETHING_V2_CLASSES = json.load(open("ssv2_classes.json", "r"))

    with torch.inference_mode():
        out_classifier = classifier(out_patch_features_pt)

    print(f"Classifier output shape: {out_classifier.shape}")

    print("Top 5 predicted class names:")
    top5_indices = out_classifier.topk(5).indices[0]
    top5_probs = F.softmax(out_classifier.topk(5).values[0]) * 100.0  # convert to percentage
    for idx, prob in zip(top5_indices, top5_probs):
        str_idx = str(idx.item())
        print(f"{SOMETHING_SOMETHING_V2_CLASSES[str_idx]} ({prob}%)")

    return
```
- **Line 82**: Load Something-Something V2 class labels
- **Line 85**: Run classifier on extracted features
- **Lines 90-91**: Get top 5 predictions with confidence scores
- **Lines 92-94**: Print human-readable class names with percentages

### Lines 99-167: Main Inference Function
```python
def run_sample_inference():
    # HuggingFace model repo name
    hf_model_name = (
        "facebook/vjepa2-vitg-fpc64-384"  # Replace with your favored model, e.g. facebook/vjepa2-vitg-fpc64-384
    )
    # Path to local PyTorch weights
    pt_model_path = "YOUR_MODEL_PATH"
```
**Lines 101-105**: Define model paths (HuggingFace repo and local PyTorch weights)

```python
    sample_video_path = "sample_video.mp4"
    # Download the video if not yet downloaded to local path
    if not os.path.exists(sample_video_path):
        video_url = "https://huggingface.co/datasets/nateraw/kinetics-mini/resolve/main/val/bowling/-WH-lxmGJVY_000005_000015.mp4"
        command = ["wget", video_url, "-O", sample_video_path]
        subprocess.run(command)
        print("Downloading video")
```
**Lines 107-113**: Download sample video if not present locally

```python
    # Initialize the HuggingFace model, load pretrained weights
    model_hf = AutoModel.from_pretrained(hf_model_name)
    model_hf.cuda().eval()

    # Build HuggingFace preprocessing transform
    hf_transform = AutoVideoProcessor.from_pretrained(hf_model_name)
    img_size = hf_transform.crop_size["height"]  # E.g. 384, 256, etc.
```
**Lines 115-121**: Initialize HuggingFace model and processor, extract image size

```python
    # Initialize the PyTorch model, load pretrained weights
    model_pt = vit_giant_xformers_rope(img_size=(img_size, img_size), num_frames=64)
    model_pt.cuda().eval()
    load_pretrained_vjepa_pt_weights(model_pt, pt_model_path)

    # Build PyTorch preprocessing transform
    pt_video_transform = build_pt_video_transform(img_size=img_size)
```
**Lines 123-129**: Initialize PyTorch model with matching dimensions and load weights

```python
    # Inference on video
    out_patch_features_hf, out_patch_features_pt = forward_vjepa_video(
        model_hf, model_pt, hf_transform, pt_video_transform
    )

    print(
        f"""
        Inference results on video:
        HuggingFace output shape: {out_patch_features_hf.shape}
        PyTorch output shape:     {out_patch_features_pt.shape}
        Absolute difference sum:  {torch.abs(out_patch_features_pt - out_patch_features_hf).sum():.6f}
        Close: {torch.allclose(out_patch_features_pt, out_patch_features_hf, atol=1e-3, rtol=1e-3)}
        """
    )
```
**Lines 131-144**: Run inference and compare outputs between model versions

```python
    # Initialize the classifier
    classifier_model_path = "YOUR_ATTENTIVE_PROBE_PATH"
    classifier = (
        AttentiveClassifier(embed_dim=model_pt.embed_dim, num_heads=16, depth=4, num_classes=174).cuda().eval()
    )
    load_pretrained_vjepa_classifier_weights(classifier, classifier_model_path)
```
**Lines 146-151**: Initialize and load pretrained classifier for Something-Something V2 (174 classes)

```python
    # Download SSV2 classes if not already present
    ssv2_classes_path = "ssv2_classes.json"
    if not os.path.exists(ssv2_classes_path):
        command = [
            "wget",
            "https://huggingface.co/datasets/huggingface/label-files/resolve/d79675f2d50a7b1ecf98923d42c30526a51818e2/"
            "something-something-v2-id2label.json",
            "-O",
            "ssv2_classes.json",
        ]
        subprocess.run(command)
        print("Downloading SSV2 classes")

    get_vjepa_video_classification_results(classifier, out_patch_features_pt)
```
**Lines 153-166**: Download class labels if needed and run classification

### Lines 169-171: Entry Point
```python
if __name__ == "__main__":
    # Run with: `python -m notebooks.vjepa2_demo`
    run_sample_inference()
```
Standard Python entry point that runs the demo when script is executed directly.

## Key Concepts

1. **VJEPA2**: A self-supervised video understanding model that learns representations by predicting masked regions
2. **Dual Implementation**: Demonstrates both HuggingFace and PyTorch implementations for comparison
3. **Video Processing**: Shows complete pipeline from video loading to feature extraction
4. **Classification**: Uses an attentive classifier for action recognition on Something-Something V2 dataset

## Usage Notes

- Replace `"YOUR_MODEL_PATH"` and `"YOUR_ATTENTIVE_PROBE_PATH"` with actual model paths
- The demo downloads sample video and class labels automatically
- Requires CUDA GPU for inference
- Compares outputs between HuggingFace and PyTorch implementations to verify consistency