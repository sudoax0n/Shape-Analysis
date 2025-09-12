# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import tifffile as tiff
import easygui as eg
import os
import numpy as np
try:
    import czifile
except ImportError:
    czifile = None

def load_image_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".czi":
        if czifile is None:
            eg.msgbox("czifile not installed. Please install with: pip install czifile", "Error")
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
            
                
            image_stack = np.squeeze(image_stack)
            return image_stack, voxel_size_x, voxel_size_y, voxel_size_z

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

            return image_stack, voxel_size_x, voxel_size_y, voxel_size_z

    else:
        eg.msgbox("Unsupported file format! Please provide a .czi or .tif/.tiff file.", "Error")
        return None, None, None, None
