# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import cv2

def draw_polygon(event, x, y, flags, param):
    global polygon_points, drawing
    if event == cv2.EVENT_LBUTTONDOWN:
        # Start a new polygon
        polygon_points = [(x, y)]
        drawing = True

    elif event == cv2.EVENT_MOUSEMOVE:
        # Add points to the polygon as the mouse moves
        if drawing:
            polygon_points.append((x, y))
    
    elif event == cv2.EVENT_LBUTTONUP:
            # Finalize the polygon when the mouse is released
        drawing = False
        polygon_points.append((x, y))
