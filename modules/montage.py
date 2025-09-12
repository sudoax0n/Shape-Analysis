# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np

def create_montage(image_stack, voxel_size_x, grid_shape=(5, 5), tile_size=(128, 128), save_path=None):
    """
    Create a montage (grid) of images from the TIFF stack with a 5-micron scale bar.

    Parameters:
    - image_stack: 3D numpy array where each slice is a 2D image.
    - voxel_size_x: The size of a voxel in the x-dimension (microns per pixel).
    - grid_shape: Tuple (rows, cols) specifying the number of rows and columns in the montage.
    - tile_size: Tuple (height, width) specifying the size of each image tile in the montage.
    - save_path: File path to save the montage image. If None, it will just display the montage.

    Returns:
    - montage: The created montage as a PIL image with the scale bar added.
    """
    n_slices = image_stack.shape[0]
    n_tiles = grid_shape[0] * grid_shape[1]
    montage_img = Image.new('L', (grid_shape[1] * tile_size[1], grid_shape[0] * tile_size[0]))  # Create a blank canvas

    # Rescale each slice and arrange them in the montage grid
    for i in range(min(n_slices, n_tiles)):
        img = Image.fromarray(image_stack[i])

        # Convert to grayscale mode 'L' if necessary
        if img.mode != 'L':
            img = img.convert('L')

        img = img.resize(tile_size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality downscaling
        row = i // grid_shape[1]
        col = i % grid_shape[1]
        montage_img.paste(img, (col * tile_size[1], row * tile_size[0]))  # Paste the resized image onto the canvas
        
    # Draw the scale bar (5 microns)
    draw = ImageDraw.Draw(montage_img)
    
    # Calculate the scale bar length in pixels (based on the voxel size in x-dimension)
    scale_bar_length_microns = 5  # 5 microns
    scale_bar_length_pixels = int(scale_bar_length_microns / voxel_size_x)

    # Position of the scale bar (bottom left corner of the montage)
    bar_height = 10  # Thickness of the scale bar in pixels
    bar_position = (50, montage_img.height - 30)  # (x, y) coordinates for the bar

    # Draw the scale bar (horizontal black rectangle)
    draw.rectangle([bar_position, (bar_position[0] + scale_bar_length_pixels, bar_position[1] + bar_height)], fill=255)

    # Add the scale bar label ("5 µm")
    font = ImageFont.load_default()
    draw.text((bar_position[0] + scale_bar_length_pixels + 10, bar_position[1] - 5), "", fill=255, font=font)

    if save_path:
        save_path += 'montage.png'
        montage_img.save(save_path)
        print(f"Montage saved at {save_path}")

    # Display montage with the scale bar
    plt.imshow(np.array(montage_img), cmap='gray')
    plt.axis('off')
    plt.show()

    return montage_img
