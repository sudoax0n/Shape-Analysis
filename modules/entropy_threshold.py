# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import numpy as np
import cv2

def entp(x):
    temp = np.multiply(x, np.log(x))
    temp[np.isnan(temp)] = 0
    return temp

def entropy_thresholding(img):
    H = cv2.calcHist([img],[0],None,[256],[0,256])
    H = H / np.sum(H)
    
    theta = np.zeros(256)
    Hf = np.zeros(256)
    Hb = np.zeros(256)

    for T in range(1,255):
        Hf[T] = - np.sum( entp(H[:T-1] / np.sum(H[1:T-1])) )
        Hb[T] = - np.sum( entp(H[T:] / np.sum(H[T:])) )
        theta[T] = Hf[T] + Hb[T]

    theta_max = np.argmax(theta)
    img_out = img #< theta_max

    return img_out
