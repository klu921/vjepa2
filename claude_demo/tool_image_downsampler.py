from PIL import Image
import os


def resize_images(frame_dir = "frames"):
    for image_path in os.listdir(frame_dir):
        if image_path.endswith(".jpg"):
            img = Image.open(image_path)
            width, height = img.size
            new_width = width/2
            new_height = height/2
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            img.save(image_path)

if __name__ == "__main__":
    resize_images()