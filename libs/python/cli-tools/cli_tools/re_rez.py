from PIL import Image
import os

def mass_resize(input_dir, output_dir, size):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            img = Image.open(os.path.join(input_dir, filename))
            img = img.resize(size, Image.ANTIALIAS)
            img.save(os.path.join(output_dir, filename))

# usage
mass_resize('path_to_input_dir', 'path_to_output_dir', (800, 600))