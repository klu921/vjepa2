import json
import os
import subprocess
import einops

import torch
from transformers import AutoModel, AutoVideoProcessor
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


HF_MODEL_NAME = "facebook/vjepa2-vitl-fpc64-256"


model = AutoModel.from_pretrained(HF_MODEL_NAME).cuda().eval()

# used cmd: ffmpeg -i video.mp4 -vf fps=1 frames/frame_%04d.jpg : to extract frames

def extract_embeddings(model, frames_path, last_frame = 3598):
    """
      Extracts embeddings from a set of frames (frames_path) using specified model (model).
      Processes each frame independently (lack temporal embeddings)
      Returns an np array of the embeddings stacked by time along first dimension

      ---

      Replace num_frames with num frames in the folder frames/
      Assumes frames are named frame_{i:04d}.jpg
      Returns an np array of the embeddings stacked by time along first dimension
    """
    embeddings = []
    processor = AutoVideoProcessor.from_pretrained(HF_MODEL_NAME)
    
    for i in range(1, last_frame + 1):
        path = f"{frames_path}/frame_{i:04d}.jpg"
        img = Image.open(path).convert("RGB")
        img = np.array(img)
        img = torch.from_numpy(img).permute(2, 0, 1)
        
        with torch.no_grad():  # no gradient accum
            x_hf = processor(img, return_tensors="pt")["pixel_values_videos"].to("cuda")
            embeddings_hf = model.get_vision_features(x_hf)
            
            # move + store in cpu for memory management
            embeddings.append(embeddings_hf.squeeze(0).cpu())
            
            # clear gpu for memory 
            del x_hf, embeddings_hf
            torch.cuda.empty_cache()
        
        if i % 100 == 0:
            print(f"Processed {i}/{last_frame} frames")
    
    all_embeddings = torch.stack(embeddings, dim=0)  # [time, patches, features]
    print(f"all_embeddings shape: {all_embeddings.shape}")
    #all_embeddings = einops.rearrange(all_embeddings, "t p f -> t (p f)")  # [time, patches*features]
    
    np.save("data_storage/all_embeddings_vitl_256.npy", all_embeddings.numpy().astype(np.float16))
    
    return all_embeddings.numpy()

def get_cossim_embeddings(embeddings, frame_path):
    """
    Gets cosine similarity embeddings between each pair of adjacent frames
    Uses tensor operations for batching instead of for-loop
    """
    # convert to tensor
    if isinstance(embeddings, np.ndarray):
        embeddings = torch.from_numpy(embeddings) # [3600, 256, features]
        
    # normalize along feature dimension
    embeddings_norm = torch.nn.functional.normalize(embeddings, p=2, dim=-1) #l2 norm
    
    # pairs_1 is the first frame of each pair, pairs_2 is the second frame of each pair
    pairs_1 = embeddings_norm[:-1]  # [3599, 256, features]
    pairs_2 = embeddings_norm[1:]   # [3599, 256, features]
    
    # dot product between corresponding patches
    patch_similarities = torch.sum(pairs_1 * pairs_2, dim=-1)  # [3599, 256]
    print(patch_similarities)

    frame_patch_pairs = np.column_stack([
        np.arange(1, len(patch_similarities) + 1),  # (1, 2, 3, ...)
        np.arange(2, len(patch_similarities) + 2),  # (2, 3, 4, ...)
        patch_similarities.numpy()  # cosine similarities
    ])

    np.save("frame_patch_pairs.npy", frame_patch_pairs)
    
    # average across all patches
    cosine_similarities = torch.mean(patch_similarities, dim=-1)  # [3599]
    #print("cosine similarities", cosine_similarities)

    # create array with frame pairs and cosine similarities
    frame_pairs = np.column_stack([
        np.arange(1, len(cosine_similarities) + 1),  # (1, 2, 3, ...)
        np.arange(2, len(cosine_similarities) + 2),  # (2, 3, 4, ...)
        cosine_similarities.numpy()  # cosine similarities
    ])

    # save the cosine similarities with frame pairs
    np.save("cosine_similarities.npy", frame_pairs)
    
    return frame_pairs

def np_to_txt(np_array, file_name):
    """
    Converts a numpy array to a text file
    Each row of the array becomes a line in the text file
    """
    # Load the .npy file and save as .txt
    data = np.load(np_array) if isinstance(np_array, str) else np_array
    np.savetxt(file_name, data, fmt='%.6f', delimiter=' ')


if __name__ == "__main__":

    frames_path = "frames"  
    last_frame = 3598  # Adjust based on your video
    
    print("Extracting embeddings...")
    embedddings = extract_embeddings(model, frames_path, last_frame)
    embeddings_file = "data_storage/all_embeddings_vitl_256.npy"
    embeddings = np.load(embeddings_file)

    # Compute cosine similarities
    print("Computing cosine similarities...")
    cosine_sims = get_cossim_embeddings(embeddings, frames_path)

    print(f"Computed cosine similarities for {len(cosine_sims)} frame pairs")    
    