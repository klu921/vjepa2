import json
import os
import subprocess
import einops

import torch
from transformers import AutoModel, AutoVideoProcessor
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans


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
    all_embeddings = einops.rearrange(all_embeddings, "t p f -> t (p f)")  # [time, patches*features]
    
    np.save("data_storage/all_embeddings.npy", all_embeddings.numpy())
    
    return all_embeddings.numpy()

def cluster_embeddings(embeddings, n_clusters = 100):
    """
    embeddings: [time, patches*features]
    n_clusters: # clusters
    load in my embeddings from all_embeddings.npy
    """
    kmeans = KMeans(n_clusters = n_clusters, random_state = 0)
    labels = kmeans.fit_predict(embeddings)
    return labels, kmeans

def get_cluster_centers(embeddings, kmeans, labels, n_clusters = 100):
    """
    Takes in embeddings, labels, # clusters
    Looks at each cluster, finds the frame closest to the cluster centroid
    Run from inside semantic_memory_baseline/ for frames pathing to be correct
    """
    representative_frames = []
    for cluster_idx in range(n_clusters):
        possible_frames = np.where(labels == cluster_idx)[0]
        cluster_embeddings = embeddings[possible_frames]
        centroid = kmeans.cluster_centers_[cluster_idx]
        distances = np.linalg.norm(cluster_embeddings - centroid, axis = 1)
        closest_frame_idx = np.argmin(distances)
        actual_frame_number = possible_frames[closest_frame_idx] + 1 # + 1 because frames are 1-indexed
        representative_frames.append({
            "frame_id": int(actual_frame_number),
            "frame_path": f"frames/frame_{actual_frame_number:04d}.jpg",
            "cluster_id": int(cluster_idx),
            "cluster_centroid": centroid.tolist(),
            })
    return representative_frames

def save_representative_frames(representative_frames, output_path = "representative_frames.json"):
    """
    Saves the representative frames to a json file
    """
    with open(output_path, "w") as f:
        json.dump(representative_frames, f)


def plot_representative_frames(representative_frames, num_clusters):
    """
    Plots the representative frames in a num_clusters // 5 x 5 grid
    """
    fig, axs = plt.subplots(num_clusters // 5, 5, figsize=(num_clusters //5 * 5, 16))
    axs = axs.flatten()
    
    sorted_frames = sorted(representative_frames, key=lambda x: x["frame_id"])

    for i, frame in enumerate(sorted_frames):
        img = Image.open(frame["frame_path"])
        axs[i].imshow(img)
        axs[i].set_title(f"Frame {frame['frame_id']}")
        axs[i].axis('off')
    
    plt.tight_layout()
    plt.savefig(f"representative_frames_{num_clusters}.png")
    plt.show()




if __name__ == "__main__":
    
    num_clusters = 30
    embeddings = extract_embeddings(model, "frames", last_frame = 10)
    print(f"embeddings shape: {embeddings.shape}")
    # embeddings = np.load("data_storage/all_embeddings.npy")
    print(f"embeddings shape: {embeddings.shape}")
    print("Embeddings loaded, clustering...")

    labels, kmeans_instance = cluster_embeddings(embeddings, n_clusters = num_clusters)
    print(f"labels shape: {labels.shape}")
    print("clustering done, getting representative frames...")

    representative_frames = get_cluster_centers(embeddings, kmeans_instance, labels, n_clusters = num_clusters)
    print(f"representative_frames: {len(representative_frames)}")

    save_representative_frames(representative_frames)
    
    representative_frames = json.load(open("representative_frames.json"))
    for item in representative_frames:
        print(item["frame_id"], item["frame_path"])

    plot_representative_frames(representative_frames, num_clusters)