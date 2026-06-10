import numpy as np
import cv2
import sys
import os
from datetime import datetime
from shapely.geometry import Polygon as ShapelyPolygon

# Ensure project modules can be loaded
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Mock easygui to prevent interactive GUI popups
import easygui as eg
eg.ynbox = lambda *args, **kwargs: True
eg.enterbox = lambda msg, title="", default="": default if default else "1.0e-6"
eg.msgbox = lambda *args, **kwargs: None

from modules.load_tif import load_image_file
from modules.hist_stretching import histogram_stretching
from modules.adjust_epsilon import adjust_epsilon_for_circularity
from modules.skeleton import generate_skeleton, prune_skeleton, calculate_vs_perimeter

def main():
    file_path = r"D:\lab-data\paper-data\syst202400052-sup-0001-movie1-dopc.tif"
    print(f"Loading file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: File does not exist at {file_path}")
        return
        
    image_stack, color_stack, voxel_size_x, voxel_size_y, voxel_size_z = load_image_file(file_path, return_color=True)
    print(f"Raw image_stack shape: {image_stack.shape}")
    image_stack = np.squeeze(image_stack)
    print(f"Squeezed image_stack shape: {image_stack.shape}")
    if image_stack.ndim == 2:
        image_stack = image_stack[np.newaxis, ...]
        
    # Scale to 0-255 uint8 as in main.py
    image_stack = (image_stack - np.min(image_stack))
    if np.max(image_stack) > 0:
        image_stack = (image_stack / np.max(image_stack) * 255.0).astype(np.uint8)
    else:
        image_stack = image_stack.astype(np.uint8)
        
    # Apply histogram stretching
    stretched_stack = histogram_stretching(image_stack)
    print(f"Stretched_stack count: {len(stretched_stack)}, shape of first slice: {stretched_stack[0].shape}")
    
    # Process frames 4 to 24 (1-indexed -> indices 3 to 23 inclusive)
    start_idx = 3
    end_idx = 23
    threshold_val = 127
    
    print("\nResolution information:")
    print(f"  Voxel Size X: {voxel_size_x / 1e-6:.6f} µm")
    print(f"  Voxel Size Z: {voxel_size_z / 1e-6:.6f} µm")
    
    print(f"\nProcessing slices {start_idx + 1} to {end_idx + 1} at threshold {threshold_val}...\n")
    
    table_rows = []
    header_str = f"{'Slice #':^8} | {'Contour Perim (µm)':^20} | {'Skel Perim (µm)':^20} | {'Difference (%)':^15}"
    divider_str = "-" * 72
    print(header_str)
    print(divider_str)
    
    contour_perims = []
    skel_perims = []
    
    for idx in range(start_idx, end_idx + 1):
        slice_img = stretched_stack[idx]
        blur = cv2.GaussianBlur(slice_img, (5, 5), 3)
        _, thresh = cv2.threshold(blur, threshold_val, 255, cv2.THRESH_TOZERO)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            row_str = f"{idx + 1:^8} | {'No contour':^20} | {'No contour':^20} | {'-':^15}"
            print(row_str)
            table_rows.append(row_str)
            continue
            
        # Get largest contour by area
        max_contour = max(contours, key=lambda c: cv2.contourArea(c))
        
        # Smooth contour (uses our robust adjust_epsilon_for_circularity)
        try:
            smoothed, _ = adjust_epsilon_for_circularity(max_contour, 0.2, 100)
        except Exception as e:
            print(f"  Smoothing error on slice {idx+1}: {e}")
            smoothed = max_contour
            
        # Convert voxel size to micrometers for correct physical perimeter display (meters * 1e6)
        voxel_size_um = voxel_size_x * 1e6

        # 1. Contour-based Perimeter (Off)
        try:
            contour_pts_arr = smoothed.reshape((-1, 2))
            shp = ShapelyPolygon(contour_pts_arr)
            c_perim_um = shp.length * voxel_size_um
        except Exception as e:
            c_perim_um = cv2.arcLength(smoothed, closed=True) * voxel_size_um
            
        # 2. Skeleton-based Perimeter (On)
        # Create hollow binary mask of the contour
        mask = np.zeros_like(thresh)
        pts_draw = smoothed.reshape((-1, 1, 2))
        cv2.drawContours(mask, [pts_draw], -1, 255, thickness=1)
        
        try:
            raw_skel = generate_skeleton(mask > 0)
            prune_pix = 15
            pruned_skel = prune_skeleton(raw_skel, prune_pix)
            s_perim_um, _ = calculate_vs_perimeter(pruned_skel, voxel_size_um)
        except Exception as e:
            print(f"  Skeleton error on slice {idx+1}: {e}")
            s_perim_um = 0.0
            
        if s_perim_um > 0:
            diff = ((c_perim_um - s_perim_um) / s_perim_um) * 100
            diff_str = f"{diff:+.2f}%"
            contour_perims.append(c_perim_um)
            skel_perims.append(s_perim_um)
        else:
            diff_str = "Error"
            
        row_str = f"{idx + 1:^8} | {c_perim_um:^20.4f} | {s_perim_um:^20.4f} | {diff_str:^15}"
        print(row_str)
        table_rows.append(row_str)
        
    avg_row = ""
    if contour_perims and skel_perims:
        avg_c = np.mean(contour_perims)
        avg_s = np.mean(skel_perims)
        avg_diff = ((avg_c - avg_s) / avg_s) * 100
        print(divider_str)
        avg_row = f"{'Average':^8} | {avg_c:^20.4f} | {avg_s:^20.4f} | {avg_diff:+.2f}%"
        print(avg_row)
        print(divider_str)
        
    # Write results to gemini.md
    gemini_path = os.path.join(os.path.dirname(__file__), "gemini.md")
    if os.path.exists(gemini_path):
        with open(gemini_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Find where to insert/replace results
        marker = "## Automated Test Verification Results"
        if marker in content:
            base_content = content.split(marker)[0]
        else:
            base_content = content.strip() + "\n\n"
            
        new_results = f"{marker}\n"
        new_results += f"Last Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        new_results += f"| Slice # | Contour Perim (µm) | Skel Perim (µm) | Difference (%) |\n"
        new_results += f"| :---: | :---: | :---: | :---: |\n"
        for idx in range(start_idx, end_idx + 1):
            slice_num = idx + 1
            row_idx = idx - start_idx
            if row_idx < len(table_rows):
                # Parse row values to make clean markdown table rows
                c_val = contour_perims[row_idx] if row_idx < len(contour_perims) else 0.0
                s_val = skel_perims[row_idx] if row_idx < len(skel_perims) else 0.0
                diff_val = ((c_val - s_val) / s_val * 100) if s_val > 0 else 0.0
                new_results += f"| {slice_num} | {c_val:.4f} | {s_val:.4f} | {diff_val:+.2f}% |\n"
                
        if contour_perims and skel_perims:
            new_results += f"| **Average** | **{avg_c:.4f}** | **{avg_s:.4f}** | **{avg_diff:+.2f}%** |\n"
            
        new_results += "\n*Note: The positive difference represents the overestimation from the grid effect and apparent membrane thickness in traditional contour measurements vs. the true bilayer centerline.*"
        
        with open(gemini_path, "w", encoding="utf-8") as f:
            f.write(base_content + new_results)
        print(f"\nSuccessfully updated test results in: {gemini_path}")

if __name__ == "__main__":
    main()
