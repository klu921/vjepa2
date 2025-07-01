#testing if the model reports same embeddings for identical frames
import torch
from transformers import AutoModel, AutoVideoProcessor
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

HF_MODEL_NAME = "facebook/vjepa2-vitl-fpc64-256"

model = AutoModel.from_pretrained(HF_MODEL_NAME).cuda().eval()



def test_identical_embeddings(model, frames_path):
    """
      Extracts embeddings from frame 0 and frame 0. 
      Tests if model extracts same embeddings for identical frames.
    """
    embeddings = []
    processor = AutoVideoProcessor.from_pretrained(HF_MODEL_NAME)
    

    #extract embeddings for frame 1, two times. Store as [2, 256, features]
    for i in range(1, 3):
        path = f"{frames_path}/frame_{1:04d}.jpg"
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
            
    
    all_embeddings = torch.stack(embeddings, dim=0)  # [time, patches, features]
    print(f"all_embeddings shape: {all_embeddings.shape}")

    embeddings_1_0, embeddings_1_1 = embeddings[0], embeddings[1]
    for i in range(embeddings_1_0.shape[0]):
        for j in range(embeddings_1_0.shape[1]):
            if embeddings_1_0[i, j] != embeddings_1_1[i, j]:
                print(f"Mismatch at index {i}, {j}")
                break
    print("Same embeddings. Model is working as predicted.")
    
    np.save("data_storage/test_identical_embeddings_1.npy", all_embeddings.numpy().astype(np.float16))
    
    return all_embeddings.numpy()

def test_embeddings_1_2(model, frames_path):
    """
      Extracts embeddings from frame 0 and frame 1
    """
    embeddings = []
    processor = AutoVideoProcessor.from_pretrained(HF_MODEL_NAME)

    for i in range(1, 3):
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
                
        
    all_embeddings = torch.stack(embeddings, dim=0)  # [time, patches, features]
    print(f"all_embeddings shape: {all_embeddings.shape}")
    #all_embeddings = einops.rearrange(all_embeddings, "t p f -> t (p f)")  # [time, patches*features]
    
    embeddings_0 = embeddings[0]
    embeddings_1 = embeddings[1]
    diff = torch.zeros_like(embeddings_0)
    for i in range(embeddings_0.shape[0]):
        diff[i] = embeddings_0[i] - embeddings_1[i]

    print(f"diff: {diff}")

    np.save("data_storage/test_embeddings_1_2.npy", all_embeddings.numpy().astype(np.float16))
    
    return all_embeddings.numpy()

if __name__ == "__main__":
    print("Testing identical embeddings")
    test_identical_embeddings(model, "frames")

    print("Testing embeddings 1 and 2")
    test_embeddings_1_2(model, "frames")