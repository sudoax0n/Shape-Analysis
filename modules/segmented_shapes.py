# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
from skimage.filters import gaussian
from skimage.segmentation import morphological_chan_vese

def new_processing(image):
    image_float = np.float32(image)
    window_size = 11  # Odd number
    poly_order = 3    # Polynomial order
    image_filtered_rows = np.copy(image_float)

    for i in range(image.shape[0]):  # Loop over each row
        image_filtered_rows[i, :] = savgol_filter(image_float[i, :], window_size, poly_order)

    # Apply the Savitzky-Golay filter to each column (axis 0)
    image_filtered = np.copy(image_filtered_rows)

    for j in range(image.shape[1]):  # Loop over each column
        image_filtered[:, j] = savgol_filter(image_filtered_rows[:, j], window_size, poly_order)

    # Convert the image back to uint8
    image = np.uint8(image_filtered)
    
    plt.imshow(image)
    plt.show()
    # Enhance contrast
    image = gaussian(image, sigma=1)

    # Level Set Segmentation
    result = morphological_chan_vese(image, num_iter=100, smoothing=3)

    # Display
    plt.figure(figsize=(8, 8))
    plt.imshow(result, cmap="gray")
    plt.title("Segmented Shapes")
    plt.axis("off")
    plt.show()
