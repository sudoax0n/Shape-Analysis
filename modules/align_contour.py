# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import cv2
import numpy as np

def calculate_centroid(contour):
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return (0, 0)
    return (M["m10"] / M["m00"], M["m01"] / M["m00"])


def align_contours(contours):
    aligned_contours = [contours[0]]
    
    reference_contour = contours[0]  # Choose the first contour as the reference
    
    #Get center for reference contour
    xx, yy = calculate_centroid(reference_contour)
    for cn in range(1,len(contours)):
        xx2 , yy2 = calculate_centroid(contours[cn])
        
        
        dx = xx - xx2
        dy = yy - yy2
        
        translation_matrix = np.float32([[1, 0, dx], [0, 1, dy]])
        rows, cols = contours[cn].shape
        aligned_image = cv2.warpAffine(contours[cn], translation_matrix, (cols, rows))
        aligned_contours.append(aligned_image)
    return aligned_contours