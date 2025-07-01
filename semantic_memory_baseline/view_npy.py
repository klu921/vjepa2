#This file is just for viewing/plotting NPY files

import numpy as np
import matplotlib.pyplot as plt

def np_to_txt(np_array, file_name):
    """
    Converts a numpy array to a text file
    Each row of the array becomes a line in the text file
    """
    # Load the .npy file and save as .txt
    data = np.load(np_array) if isinstance(np_array, str) else np_array
    np.savetxt(file_name, data, fmt='%.6f', delimiter=' ')

def view_npy(np_array):
    """
    View a numpy array
    """
    data = np.load(np_array) if isinstance(np_array, str) else np_array
    print("shape", data.shape)
    print("first 10 rows", data[:10])


def plot_npy(np_array):
    """
    plots (frame i, frame i+1) cosine similarity in a graph.
    """
    data = np.load(np_array) if isinstance(np_array, str) else np_array
    plt.figure(figsize=(20, 6))
    plt.plot(data[:, 0], data[:, 2])
    plt.xlabel("Frame")
    plt.ylabel("Cosine Similarity")
    plt.title("Cosine Similarity between Frame Pairs")
    plt.savefig("cosine_similarity_plot.png")
    plt.show()


if __name__ == "__main__":
    plot_npy("cosine_similarities.npy")
    #view_npy("data_storage/all_embeddings_vitl_256.npy")