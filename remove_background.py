import sys
import os
from rembg import remove
from PIL import Image

print("start")

# Read image path from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python3 background_removal.py <image_path>")
    sys.exit(1)

input_path = sys.argv[1]  # Get the image path from arguments

# Ensure the file exists
if not os.path.exists(input_path):
    print(f"Error: The selected image '{input_path}' does not exist.")
    sys.exit(1)

# Get input image directory and create 'output' folder inside it
input_dir = os.path.dirname(input_path)
output_dir = os.path.join(input_dir, "Remove_background")
os.makedirs(output_dir, exist_ok=True)

# Set output file path
output_path = os.path.join(output_dir, os.path.splitext(os.path.basename(input_path))[0] + ".png")

# Open image and remove background
with Image.open(input_path) as img:
    output = remove(img)
    output.save(output_path)

print(f"Processed: {input_path} -> {output_path}")
