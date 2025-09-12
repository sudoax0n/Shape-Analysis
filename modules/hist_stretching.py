# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import numpy as np

def histogram_stretching(image_stack):
    new_stack = []
    """
    Perform histogram stretching on a grayscale image.

    Parameters:
        image (numpy.ndarray): Input grayscale image.

    Returns:
        numpy.ndarray: Image after histogram stretching.
    """
    for image in image_stack:
    # Find the minimum and maximum pixel intensity values
        min_val = np.min(image)
        max_val = np.max(image)

        # Stretch the pixel values
        stretched = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        
        new_stack.append(stretched)

    return new_stack
