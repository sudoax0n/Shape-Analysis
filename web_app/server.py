# The web app backend is built by Abhinav (GitHub: https://github.com/sudoax0n), Soft Matter Biophysics Lab
# Reuses modules written by Tanmay Pandey
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Abhinav: ms24115@gmail.com or https://github.com/sudoax0n

import sys
import os
import io
import base64
import numpy as np
import cv2
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from skimage import measure
import plotly.graph_objects as go
from shapely.geometry import Polygon as ShapelyPolygon
from scipy.ndimage import zoom

# Add parent directory to path to reuse existing biophysics modules
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_DIR)

from modules.load_tif import load_image_file, convert_to_grayscale_3d
from modules.hist_stretching import histogram_stretching
from modules.align_contour import align_contours
from modules.shape_paramters import calculate_shape_parameters
from modules.three_dimensional_map import calculate_surface_area_volume

app = FastAPI(title="SMBL - Shape Analysis Web App")

# In-memory session store for processed images
# In a real environment, we'd use a session manager, but global store works perfectly for local single-user use.
SESSION = {
    "file_path": None,
    "raw_stack": None,       # 3D grayscale stack (Z, Y, X)
    "voxel_x": 1e-6,
    "voxel_y": 1e-6,
    "voxel_z": 1e-6,
    "preprocessed": None,   # normalized and stretched stack
    "sliced_stack": None,   # cropped stack in Z range
    "roi_cropped": None,    # stack with ROI crop applied
    "z_min": 0,
    "z_max": 0,
}

# Helper to encode raw numpy image slice as Base64 PNG for browser rendering
def encode_image_base64(image_2d: np.ndarray) -> str:
    img = np.asarray(image_2d, dtype=np.uint8)
    _, buffer = cv2.imencode('.png', img)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="index.html not found under templates/")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/upload")
async def upload_microscope_file(file: UploadFile = File(...)):
    # Save the file temporarily to load it
    temp_dir = os.path.join(PARENT_DIR, "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as f:
        f.write(await file.read())
        
    try:
        # Load stack and voxel information using load_tif module
        image_stack, vx, vy, vz = load_image_file(temp_path)
        if image_stack is None:
            raise HTTPException(status_code=400, detail="Failed to load file.")
            
        # Standardize stack
        image_stack = convert_to_grayscale_3d(image_stack)
        
        # Scale to uint8
        image_stack = (image_stack - np.min(image_stack))
        if np.max(image_stack) > 0:
            image_stack = (image_stack / np.max(image_stack) * 255.0).astype(np.uint8)
        else:
            image_stack = image_stack.astype(np.uint8)
            
        # Store in session
        SESSION["file_path"] = temp_path
        SESSION["raw_stack"] = image_stack
        SESSION["voxel_x"] = vx
        SESSION["voxel_y"] = vy
        SESSION["voxel_z"] = vz
        
        # Apply initial histogram stretching
        SESSION["preprocessed"] = np.stack(histogram_stretching(image_stack), axis=0)
        
        # Reset defaults
        SESSION["sliced_stack"] = SESSION["preprocessed"].copy()
        SESSION["roi_cropped"] = SESSION["preprocessed"].copy()
        SESSION["z_min"] = 0
        SESSION["z_max"] = len(image_stack) - 1
        
        # Previews
        first_frame_b64 = encode_image_base64(SESSION["preprocessed"][0])
        last_frame_b64 = encode_image_base64(SESSION["preprocessed"][-1])
        
        return JSONResponse(content={
            "filename": file.filename,
            "voxel_x": vx,
            "voxel_y": vy,
            "voxel_z": vz,
            "total_frames": len(image_stack),
            "height": image_stack.shape[1],
            "width": image_stack.shape[2],
            "first_frame_preview": first_frame_b64,
            "last_frame_preview": last_frame_b64
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

class SliceRangeRequest(BaseModel):
    z_min: int
    z_max: int

@app.post("/api/slice")
async def slice_stack(req: SliceRangeRequest):
    if SESSION["preprocessed"] is None:
        raise HTTPException(status_code=400, detail="No active session. Please upload a file first.")
        
    total = len(SESSION["preprocessed"])
    if req.z_min < 0 or req.z_max >= total or req.z_min > req.z_max:
        raise HTTPException(status_code=400, detail="Invalid Z slicing indices.")
        
    SESSION["z_min"] = req.z_min
    SESSION["z_max"] = req.z_max
    
    # Sliced stack
    SESSION["sliced_stack"] = SESSION["preprocessed"][req.z_min : req.z_max + 1].copy()
    SESSION["roi_cropped"] = SESSION["sliced_stack"].copy()
    
    # Previews of new range edges
    first_b64 = encode_image_base64(SESSION["sliced_stack"][0])
    last_b64 = encode_image_base64(SESSION["sliced_stack"][-1])
    
    return JSONResponse(content={
        "total_sliced_frames": len(SESSION["sliced_stack"]),
        "first_frame_preview": first_b64,
        "last_frame_preview": last_b64
    })

# Supports applying ROI either globally to all slices or per-slice via coordinates
class BoundingBox(BaseModel):
    ymin: int
    ymax: int
    xmin: int
    xmax: int
    global_roi: bool = True
    frame_idx: Optional[int] = 0

@app.post("/api/apply_roi")
async def apply_roi(req: BoundingBox):
    if SESSION["sliced_stack"] is None:
        raise HTTPException(status_code=400, detail="No sliced stack available.")
        
    sliced = SESSION["sliced_stack"].copy()
    ny, nx = sliced.shape[1], sliced.shape[2]
    
    # Verify bounds
    ymin, ymax = max(0, req.ymin), min(ny, req.ymax)
    xmin, xmax = max(0, req.xmin), min(nx, req.xmax)
    
    # Construct mask
    mask = np.zeros((ny, nx), dtype=np.uint8)
    mask[ymin:ymax, xmin:xmax] = 255
    
    if req.global_roi:
        for idx in range(len(sliced)):
            sliced[idx][mask == 0] = 0
        SESSION["roi_cropped"] = sliced
        print(f"Applied Global Bounding Box ROI: x:[{xmin}, {xmax}], y:[{ymin}, {ymax}]")
    else:
        # Per frame crop
        if req.frame_idx is not None and 0 <= req.frame_idx < len(sliced):
            sliced[req.frame_idx][mask == 0] = 0
            SESSION["roi_cropped"] = sliced
            print(f"Applied ROI on slice {req.frame_idx}: x:[{xmin}, {xmax}], y:[{ymin}, {ymax}]")
            
    # Return preview of current active cropped frame
    preview_idx = req.frame_idx if (req.frame_idx and 0 <= req.frame_idx < len(sliced)) else 0
    preview_b64 = encode_image_base64(SESSION["roi_cropped"][preview_idx])
    
    return JSONResponse(content={
        "success": True,
        "preview_image": preview_b64
    })

@app.get("/api/frame/{idx}")
async def get_frame(idx: int):
    if SESSION["roi_cropped"] is None:
        raise HTTPException(status_code=400, detail="No stack loaded.")
    if idx < 0 or idx >= len(SESSION["roi_cropped"]):
        raise HTTPException(status_code=404, detail="Frame index out of bounds.")
        
    frame_b64 = encode_image_base64(SESSION["roi_cropped"][idx])
    return JSONResponse(content={"frame_image": frame_b64})

class SegmentPreviewRequest(BaseModel):
    frame_idx: int
    threshold: int

@app.post("/api/segment/preview")
async def segment_preview(req: SegmentPreviewRequest):
    if SESSION["roi_cropped"] is None:
        raise HTTPException(status_code=400, detail="No stack loaded.")
    if req.frame_idx < 0 or req.frame_idx >= len(SESSION["roi_cropped"]):
        raise HTTPException(status_code=404, detail="Frame out of bounds.")
        
    img = SESSION["roi_cropped"][req.frame_idx]
    
    # Duplicate blur + threshold pipeline from baseline main.py
    blur = cv2.GaussianBlur(img, (5, 5), 3)
    _, thresh = cv2.threshold(blur, req.threshold, 255, cv2.THRESH_TOZERO)
    
    # Auto-contour largest contour
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    contour_pts = []
    circularity = 0.0
    area = 0.0
    perimeter = 0.0
    
    if contours:
        max_contour = max(contours, key=lambda c: cv2.arcLength(c, closed=True))
        
        # circularity smoothing
        try:
            from modules.adjust_epsilon import adjust_epsilon_for_circularity
            smoothed_contour, _ = adjust_epsilon_for_circularity(max_contour, 0.2, 100)
            if smoothed_contour is not None and len(smoothed_contour) > 0:
                max_contour = smoothed_contour
        except Exception:
            pass
            
        contour_pts = max_contour[:, 0, :].tolist()  # [[x, y], ...]
        
        # Calculate shape characteristics
        try:
            area = float(cv2.contourArea(max_contour))
            perimeter = float(cv2.arcLength(max_contour, closed=True))
            if perimeter > 0:
                circularity = (4 * np.pi * area) / (perimeter ** 2)
        except Exception:
            pass
            
    return JSONResponse(content={
        "contour": contour_pts,
        "circularity": circularity,
        "area": area,
        "perimeter": perimeter
    })

class SliceContour(BaseModel):
    frame_idx: int
    contour: List[List[int]]  # custom list of [[x, y], ...]
    threshold: int            # threshold value used for this slice

class FinalSaveRequest(BaseModel):
    slices: List[SliceContour]
    h_value: int = 0

@app.post("/api/segment/save")
async def save_final_analysis(req: FinalSaveRequest):
    if SESSION["roi_cropped"] is None:
        raise HTTPException(status_code=400, detail="No stack loaded.")
        
    stack = SESSION["roi_cropped"]
    vx = SESSION["voxel_x"]
    vy = SESSION["voxel_y"]
    vz = SESSION["voxel_z"]
    file_path = SESSION["file_path"]
    
    contour_stack = []
    
    data = {
        'area': [],
        'perimeter': [],
        'Ellipse_major_axis_length': [],
        'Ellipse_minor_axis_length': [],
        'Ellipse_eccentricity': [],
        'Ellipse_aspect_ratio': [],
        'Ellipse_circularity': [],
        'Ellipse_solidity': [],
        'Ellipse_area': [],
        'Ellipse_perimeter': [],
        'Ellipse_angle': [],
        'volume': [],
        'surface_area': [],
        'area_pix': [],
        'perim_pix': []
    }
    
    for idx in range(len(stack)):
        zero_image = np.zeros_like(stack[idx])
        
        # Get contour from request or calculate it if empty using its threshold
        pts = None
        for item in req.slices:
            if item.frame_idx == idx:
                if len(item.contour) > 0:
                    pts = np.array(item.contour, dtype=np.int32)
                else:
                    # Auto-calculate on backend using the threshold!
                    img = stack[idx]
                    blur = cv2.GaussianBlur(img, (5, 5), 3)
                    _, thresh = cv2.threshold(blur, item.threshold, 255, cv2.THRESH_TOZERO)
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        max_contour = max(contours, key=lambda c: cv2.arcLength(c, closed=True))
                        try:
                            from modules.adjust_epsilon import adjust_epsilon_for_circularity
                            smoothed, _ = adjust_epsilon_for_circularity(max_contour, 0.2, 100)
                            if smoothed is not None and len(smoothed) > 0:
                                max_contour = smoothed
                        except Exception:
                            pass
                        pts = max_contour[:, 0, :]
                break
        
        if pts is not None and len(pts) > 0:
            pts_cv2 = pts.reshape((-1, 1, 2))
            
            # Fill mask
            cv2.drawContours(zero_image, [pts_cv2], -1, (255, 255, 255), thickness=-1)
            contour_stack.append(zero_image)
            
            # 2D Geometry parameters
            try:
                shp = ShapelyPolygon(pts)
                area = shp.area
                perim = shp.length
            except Exception:
                try:
                    area = cv2.contourArea(pts_cv2)
                    perim = cv2.arcLength(pts_cv2, closed=True)
                except Exception:
                    area = 0
                    perim = 0
                
            shape_params = None
            try:
                shape_params = calculate_shape_parameters(pts_cv2, vx, vy, vz)
            except Exception:
                pass
                
            # Append parameters
            if shape_params:
                for key in shape_params.keys():
                    data_key = f"Ellipse_{key}"
                    if data_key in data:
                        data[data_key].append(shape_params[key])
            else:
                for key in data.keys():
                    if key.startswith("Ellipse_"):
                        data[key].append(np.nan)
                        
            data['area'].append(area * (vx ** 2))
            data['area_pix'].append(area)
            data['perim_pix'].append(perim)
            data['volume'].append(area * (vx ** 2) * vz)
            data['perimeter'].append(perim * vx)
            data['surface_area'].append(perim * vx * vz)
            
        else:
            contour_stack.append(zero_image)
            # Empty frame parameters
            for k in data.keys():
                data[k].append(0.0)
                
    # Align contours vertically
    try:
        contour_stack = align_contours(contour_stack)
    except Exception as e:
        print(f"Alignment skipped: {e}")
        
    surface_3d = np.nan
    vol_3d = np.nan
    plotly_html = ""
    
    if len(contour_stack) > 0:
        contour_stack_3d = np.stack(contour_stack, axis=0)
        contour_stack_3d = (contour_stack_3d > 0).astype(np.uint8)
        
        # Marching cubes 3D surface
        try:
            # Downsample for Plotly speed
            try:
                downsampled_stack = zoom(contour_stack_3d, (0.5, 0.5, 0.5), order=1)
            except Exception:
                downsampled_stack = contour_stack_3d
                
            verts, faces, _, _ = measure.marching_cubes(downsampled_stack, level=0.5, spacing=(vz, vy, vx))
            
            # Apply missing slices gap closure (h-value)
            if req.h_value > 0:
                depth = verts[:, 2].max() - verts[:, 2].min()
                for i in range(req.h_value):
                    new_z = verts[:, 2].max() + (i + 1) * (depth / (req.h_value + 1))
                    new_verts = verts.copy()
                    new_verts[:, 2] = new_z
                    verts = np.vstack((verts, new_verts))
                    faces = np.vstack((faces, faces + len(new_verts)))
                    
            surface_3d, vol_3d = calculate_surface_area_volume(verts, faces)
            
            # Construct interactive Mesh3D Plotly object
            fig = go.Figure(data=[go.Mesh3d(
                x=verts[:, 0],
                y=verts[:, 1],
                z=verts[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                opacity=0.9,
                color='cyan',
                flatshading=True
            )])
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                scene=dict(
                    xaxis_title="X (μm)",
                    yaxis_title="Y (μm)",
                    zaxis_title="Z (μm)",
                    xaxis=dict(gridcolor='rgba(255,255,255,0.15)', backgroundcolor='rgba(0,0,0,0)', showbackground=True),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.15)', backgroundcolor='rgba(0,0,0,0)', showbackground=True),
                    zaxis=dict(gridcolor='rgba(255,255,255,0.15)', backgroundcolor='rgba(0,0,0,0)', showbackground=True)
                )
            )
            
            plotly_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
            
        except Exception as e:
            print(f"Marching Cubes skipped or failed: {e}")
            
    # Save CSV output next to original uploaded file
    data['3D_Surface_Area'] = [surface_3d] * len(stack)
    data['3D_Volume'] = [vol_3d] * len(stack)
    
    df = pd.DataFrame(data)
    csv_path = f"{file_path}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved completed shape metrics to {csv_path}")
    
    return JSONResponse(content={
        "csv_path": csv_path,
        "surface_3d": float(surface_3d) if not np.isnan(surface_3d) else 0.0,
        "volume_3d": float(vol_3d) if not np.isnan(vol_3d) else 0.0,
        "plotly_div": plotly_html
    })

if __name__ == "__main__":
    import uvicorn
    # Set standard local port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
