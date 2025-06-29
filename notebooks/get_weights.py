import torch
import os

# Set torch hub cache directory to local data folder
os.environ['TORCH_HOME'] = '/data/LCVR_weights'

# preprocessor
processor = torch.hub.load('facebookresearch/vjepa2', 'vjepa2_preprocessor')
# models
vjepa2_vit_large = torch.hub.load('facebookresearch/vjepa2', 'vjepa2_vit_large')
vjepa2_vit_huge = torch.hub.load('facebookresearch/vjepa2', 'vjepa2_vit_huge')
vjepa2_vit_giant = torch.hub.load('facebookresearch/vjepa2', 'vjepa2_vit_giant')
vjepa2_vit_giant_384 = torch.hub.load('facebookresearch/vjepa2', 'vjepa2_vit_giant_384')

# Download SSV2 classifier from HuggingFace
from huggingface_hub import snapshot_download
snapshot_download(repo_id='facebook/vjepa2-vitg-fpc64-384-ssv2', cache_dir='/data/LCVR_weights')

