# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import cv2
import numpy as np

def calculate_shape_parameters(contour,x,y,z):
    # Fit an ellipse to the contour if there are enough points
    if len(contour) < 5:
        return None  # Not enough points to fit an ellipse
    
    ellipse = cv2.fitEllipse(contour)
    
    # Extract the ellipse properties
    (center, axes, angle) = ellipse
    major_axis_length = max(axes)*x
    minor_axis_length = min(axes)*y
    
    # Calculate the eccentricity
    eccentricity = np.sqrt(1 - (minor_axis_length ** 2) / (major_axis_length ** 2))
    
    # Calculate contour area and perimeter
    area = cv2.contourArea(contour)*x*y
    perimeter = cv2.arcLength(contour, closed=True)*x
    
    # Calculate circularity (avoiding division by zero)
    if perimeter > 0:
        circularity = (4 * np.pi * area) / (perimeter ** 2)
    else:
        circularity = 0
    
    # Calculate aspect ratio (major axis / minor axis)
    aspect_ratio = major_axis_length / minor_axis_length
    
    # Calculate the convex hull area (for solidity)
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    
    # Calculate solidity
    if hull_area > 0:
        solidity = area / hull_area
    else:
        solidity = 0
    
    # Return all parameters in a dictionary
    shape_params = {
        'major_axis_length': major_axis_length,
        'minor_axis_length': minor_axis_length,
        'eccentricity': eccentricity,
        'aspect_ratio': aspect_ratio,
        'circularity': circularity,
        'solidity': solidity,
        'area': area,
        'perimeter': perimeter,
        'angle': angle  # Angle of the ellipse
    }
    
    return shape_params