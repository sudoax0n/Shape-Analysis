# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Modified and extended by Abhinav (GitHub: https://github.com/sudoax0n), Soft Matter Biophysics Lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Abhinav: ms24115@gmail.com or https://github.com/sudoax0n
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import tifffile as tiff
import easygui as eg
import os
import numpy as np
import cv2
try:
    import czifile
except ImportError:
    czifile = None

def convert_to_grayscale_3d(image_stack):
    image_stack = np.asarray(image_stack)
    
    # 1. Standardize 2D grayscale array to 3D shape (1, Y, X)
    if image_stack.ndim == 2:
        return image_stack[np.newaxis, ...]
        
    # 2. Check if 3D array is a single RGB/RGBA image of shape (Y, X, C)
    if image_stack.ndim == 3:
        if image_stack.shape[-1] in [3, 4]:
            if image_stack.shape[-1] == 3:
                gray = cv2.cvtColor(image_stack, cv2.COLOR_RGB2GRAY)
            else:
                gray = cv2.cvtColor(image_stack, cv2.COLOR_RGBA2GRAY)
            return gray[np.newaxis, ...]
        else:
            # Already (Z, Y, X) grayscale
            return image_stack
            
    # 3. Check if 4D array, e.g. (Z, Y, X, C) or (Z, C, Y, X)
    if image_stack.ndim == 4:
        # If the last dimension is 3 or 4, it is (Z, Y, X, C)
        if image_stack.shape[-1] in [3, 4]:
            gray_slices = []
            for i in range(image_stack.shape[0]):
                slice_img = image_stack[i]
                if image_stack.shape[-1] == 3:
                    gray = cv2.cvtColor(slice_img, cv2.COLOR_RGB2GRAY)
                else:
                    gray = cv2.cvtColor(slice_img, cv2.COLOR_RGBA2GRAY)
                gray_slices.append(gray)
            return np.stack(gray_slices, axis=0)
        # If the second dimension is 3 or 4, it is (Z, C, Y, X)
        elif image_stack.shape[1] in [3, 4]:
            gray_slices = []
            for i in range(image_stack.shape[0]):
                slice_img = np.transpose(image_stack[i], (1, 2, 0)) # (C, Y, X) -> (Y, X, C)
                if image_stack.shape[1] == 3:
                    gray = cv2.cvtColor(slice_img, cv2.COLOR_RGB2GRAY)
                else:
                    gray = cv2.cvtColor(slice_img, cv2.COLOR_RGBA2GRAY)
                gray_slices.append(gray)
            return np.stack(gray_slices, axis=0)
            
    # If 5D or higher, squeeze all single dimensions and recurse
    if image_stack.ndim > 4:
        squeezed = np.squeeze(image_stack)
        if squeezed.ndim < image_stack.ndim:
            return convert_to_grayscale_3d(squeezed)
            
    return image_stack

def convert_to_color_3d(image_stack):
    image_stack = np.asarray(image_stack)
    
    # 1. Standardize 2D grayscale array to 3D color shape (1, Y, X, 3)
    if image_stack.ndim == 2:
        color_img = cv2.cvtColor(image_stack, cv2.COLOR_GRAY2RGB)
        return color_img[np.newaxis, ...]
        
    # 2. Check if 3D array
    if image_stack.ndim == 3:
        # Check if single RGB/RGBA image of shape (Y, X, C)
        if image_stack.shape[-1] in [3, 4]:
            return image_stack[np.newaxis, ...]
        else:
            # Grayscale stack (Z, Y, X). Convert each slice to RGB
            color_slices = []
            for i in range(image_stack.shape[0]):
                color_slices.append(cv2.cvtColor(image_stack[i], cv2.COLOR_GRAY2RGB))
            return np.stack(color_slices, axis=0)
            
    # 3. Check if 4D array, e.g. (Z, Y, X, C) or (Z, C, Y, X)
    if image_stack.ndim == 4:
        # If the last dimension is 3 or 4, it is already (Z, Y, X, C)
        if image_stack.shape[-1] in [3, 4]:
            return image_stack
        # If the second dimension is 3 or 4, it is (Z, C, Y, X)
        elif image_stack.shape[1] in [3, 4]:
            color_slices = []
            for i in range(image_stack.shape[0]):
                slice_img = np.transpose(image_stack[i], (1, 2, 0)) # (C, Y, X) -> (Y, X, C)
                color_slices.append(slice_img)
            return np.stack(color_slices, axis=0)
            
    # If 5D or higher, squeeze all single dimensions and recurse
    if image_stack.ndim > 4:
        squeezed = np.squeeze(image_stack)
        if squeezed.ndim < image_stack.ndim:
            return convert_to_color_3d(squeezed)
            
    # Fallback: duplicate grayscale channels
    gray = convert_to_grayscale_3d(image_stack)
    color_slices = []
    for i in range(gray.shape[0]):
        color_slices.append(cv2.cvtColor(gray[i], cv2.COLOR_GRAY2RGB))
    return np.stack(color_slices, axis=0)

def load_image_file(file_path, return_color=False):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".czi":
        if czifile is None:
            eg.msgbox("czifile not installed. Please install with: pip install czifile", "Error")
            if return_color:
                return None, None, None, None, None
            return None, None, None, None

        with czifile.CziFile(file_path) as czi:
            image_stack = czi.asarray()
            metadata = czi.metadata()

            # Default None, we will ask user later if missing
            voxel_size_x = voxel_size_y = voxel_size_z = 1e-6

            # Try to parse voxel sizes from metadata if available
            if "ScalingX" in metadata:
                voxel_size_x = float(metadata["ScalingX"])
            if "ScalingY" in metadata:
                voxel_size_y = float(metadata["ScalingY"])
            if "ScalingZ" in metadata:
                voxel_size_z = float(metadata["ScalingZ"])

            # Confirm with user
            voxel_size_x = float(eg.enterbox(f"Voxel size X (default {voxel_size_x})", "Confirm voxel size", str(voxel_size_x)))
            voxel_size_y = float(eg.enterbox(f"Voxel size Y (default {voxel_size_y})", "Confirm voxel size", str(voxel_size_y)))
            voxel_size_z = float(eg.enterbox(f"Voxel size Z (default {voxel_size_z})", "Confirm voxel size", str(voxel_size_z)))
            
            gray_stack = convert_to_grayscale_3d(image_stack)
            if return_color:
                color_stack = convert_to_color_3d(image_stack)
                return gray_stack, color_stack, voxel_size_x, voxel_size_y, voxel_size_z
            return gray_stack, voxel_size_x, voxel_size_y, voxel_size_z

    elif ext in [".tif", ".tiff"]:
        with tiff.TiffFile(file_path) as tif:
            image_stack = tif.asarray()
            voxel_size_x = voxel_size_y = voxel_size_z = 1e-6

            # Try extracting from tags
            if 'XResolution' in tif.pages[0].tags:
                x_res = tif.pages[0].tags['XResolution'].value
                voxel_size_x = 1 / x_res[0]
            if 'YResolution' in tif.pages[0].tags:
                y_res = tif.pages[0].tags['YResolution'].value
                voxel_size_y = 1 / y_res[0]
            if 'ImageDescription' in tif.pages[0].tags:
                description = tif.pages[0].tags['ImageDescription'].value
                if "spacing" in description:
                    voxel_size_z = float(description.split("spacing=")[1].split()[0])

            # Ask user to confirm or override
            if not voxel_size_x or not eg.ynbox(f"Detected voxel size X = {voxel_size_x}. Use this?", "Confirm"):
                voxel_size_x = float(eg.enterbox("Enter voxel size X", "SMBL"))
            if not voxel_size_y or not eg.ynbox(f"Detected voxel size Y = {voxel_size_y}. Use this?", "Confirm"):
                voxel_size_y = float(eg.enterbox("Enter voxel size Y", "SMBL"))
            if not voxel_size_z or not eg.ynbox(f"Detected voxel size Z = {voxel_size_z}. Use this?", "Confirm"):
                voxel_size_z = float(eg.enterbox("Enter voxel size Z", "SMBL"))

            gray_stack = convert_to_grayscale_3d(image_stack)
            if return_color:
                color_stack = convert_to_color_3d(image_stack)
                return gray_stack, color_stack, voxel_size_x, voxel_size_y, voxel_size_z
            return gray_stack, voxel_size_x, voxel_size_y, voxel_size_z

    else:
        eg.msgbox("Unsupported file format! Please provide a .czi or .tif/.tiff file.", "Error")
        if return_color:
            return None, None, None, None, None
        return None, None, None, None
