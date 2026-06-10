# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import cv2 
import numpy as np

def adjust_epsilon_for_circularity(contour, desired_circularity=0.8, max_iterations=100, tolerance=1e-3):
    """
    Adjust the epsilon coefficient in cv2.approxPolyDP to ensure that the circularity
    of the contour remains above the desired circularity (default 0.8).

    Parameters:
    - contour: The original contour to be smoothed.
    - desired_circularity: The target circularity value (default is 0.8).
    - max_iterations: Maximum number of iterations to adjust epsilon.
    - tolerance: The allowable difference between the desired and calculated circularity.

    Returns:
    - smoothed_contour: The contour after smoothing that meets the circularity condition.
    - final_circularity: The circularity of the smoothed contour.
    """
    def calculate_circularity(c):
        if c is None or len(c) < 3:
            return 0
        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, closed=True)
        if perimeter == 0:  # Avoid division by zero
            return 0
        try:
            circularity = (4 * np.pi * area) / (perimeter ** 2)
            return circularity
        except:
            return 0

    orig_circularity = calculate_circularity(contour)
    if orig_circularity >= desired_circularity or len(contour) < 4:
        return contour, orig_circularity

    # Initialize epsilon as a small value relative to the contour's perimeter
    epsilon_coefficient = 0.001
    perimeter = cv2.arcLength(contour, closed=True)
    epsilon = epsilon_coefficient * perimeter

    last_valid_contour = contour
    last_valid_circularity = orig_circularity

    # Iterate and adjust epsilon until we meet the circularity condition or reach max iterations
    for _ in range(max_iterations):
        # Smooth the contour with the current epsilon
        smoothed_contour = cv2.approxPolyDP(contour, epsilon, closed=True)

        if smoothed_contour is None or len(smoothed_contour) < 4:
            # Collapsed! Stop simplifying further and return the last valid contour.
            break

        # Calculate the circularity of the smoothed contour
        circularity = calculate_circularity(smoothed_contour)

        # Track the last valid contour
        last_valid_contour = smoothed_contour
        last_valid_circularity = circularity

        # Check if the circularity is above the desired threshold
        if circularity >= desired_circularity or abs(circularity - desired_circularity) <= tolerance:
            return smoothed_contour, circularity

        # If not, adjust epsilon by decreasing it to retain more points (smoother contours reduce circularity)
        epsilon_coefficient *= 1.1  # Increase epsilon slightly
        epsilon = epsilon_coefficient * perimeter

    # If no satisfactory result is found, return the last valid contour (which has >= 4 points)
    return last_valid_contour, last_valid_circularity
