# Codebase Improvements Changelog

This document lists the technical changes and bug fixes made to the Shape Analysis Suite.

---

## Desktop GUI Patches and Calibration

### 1. Voxel Size Unit Calibration
*   **Files**: `modules/load_tif.py`
*   **Problem**: The resolution tags (like `XResolution` and `YResolution`) extracted from TIFF files represent pixels per micron. The original loader computed resolution as `1 / resolution` (e.g. `0.1` or `0.37`), treating the output as SI meters. This was off by six orders of magnitude, causing the 3D visualizer axes to render in nanometers and corrupting surface area and volume metrics.
*   **Solution**: We corrected the tag parser to multiply the calculated pixel size by `1e-6` (e.g. `(1 / resolution) * 1e-6`), scaling the units from microns to meters. This aligns all downstream physical measurements.

### 2. Grayscale Stack Normalization
*   **Files**: `modules/load_tif.py`
*   **Problem**: Loading RGB or multi-channel files (.tif, .tiff, or .czi) crashed the OpenCV Gaussian Blur and Otsu thresholding code. The script raised a `CV_8UC1` assertion error because the thresholding functions required single-channel grayscale arrays.
*   **Solution**: We added a conversion utility (`convert_to_grayscale_3d`) to standardize raw multi-channel files into a single grayscale channel before processing.

### 3. Canvas Reset and Memory Leakage
*   **Files**: `modules/contour_paintbrush.py`
*   **Problem**: The Matplotlib paintbrush tool leaked memory and lagged during Z-slice navigation because old bounding boxes and adjustment handles accumulated on the screen.
*   **Solution**: We updated `show_frame`, `set_tool`, and `reset_roi` to clear the axes using `self.ax.clear()`. We configured the tool to call `.set_visible(False)` and disconnect active selector event listeners during transitions.

### 4. Interactive Range Selection Navigation
*   **Files**: `modules/slice.py`
*   **Problem**: In the range selection step, users had to click the window manager's red "X" to progress. This interrupted the script execution.
*   **Solution**: We added a 'Confirm & Next' button to the bottom of the plot. Clicking the button closes the plot window and advances the execution.

### 5. Color Range Selector Display
*   **Files**: `modules/slice.py`, `main.py`
*   **Problem**: The grayscale normalization change stripped all color channels, causing the range selector plot to display images in black and white.
*   **Solution**: We added a `display_stack` parameter to `sliceit` in `slice.py` and passed the normalized `color_stack` to it in `main.py`. This uses the color stack for visual rendering in the GUI while executing range selection calculations on the grayscale stack.

### 6. Global ROI Crop Box Projection
*   **Files**: `modules/contour_paintbrush.py`
*   **Problem**: Users had to draw and confirm a cropping bounding box for every frame in the Z-stack.
*   **Solution**: We added an 'Apply Globally' button linked to `apply_globally()`. This function copies the crop mask coordinates from the current slice to the entire stack.

### 7. DataFrame Alignment Crash
*   **Files**: `main.py`
*   **Problem**: Skipping frames crashed the spreadsheet exporter with a `ValueError`. The loop did not append values for skipped frames, leaving some column arrays shorter than others.
*   **Solution**: We patched the loop in `main.py` to populate skipped slices with `np.nan` values. This aligns column lengths.

### 8. Short Stack Meshing
*   **Files**: `main.py`
*   **Problem**: Downsampling the Z-axis by 50% to speed up rendering left short stacks (few Z-slices) with too few points, crashing the 3D mesh generator.
*   **Solution**: We configured the generator to check if the stack contains more than 20 Z-slices before downsampling the Z-axis. Short stacks bypass downsampling to preserve the 3D structure.

### 9. Contour Area Selection Optimization
*   **Files**: `main.py`
*   **Problem**: The global thresholding pathway picked contours by `cv2.arcLength` instead of `cv2.contourArea`. This selected thin noise lines instead of the vesicle shell.
*   **Solution**: We swapped `arcLength` for `contourArea` inside the global threshold path to select contours by area.

### 10. "Skip Frame" Navigation Button
*   **Files**: `main.py`
*   **Problem**: The threshold selector loop did not let users skip frames to reach better equatorial slices first.
*   **Solution**: We added a "Skip Frame" button to the interactive threshold selector to let users skip dim pole slices at the start of the stack.

### 11. Retroactive Global Threshold Application
*   **Files**: `main.py`
*   **Problem**: Skipped initial frames did not receive the global threshold, causing missing sections in the 3D reconstruction.
*   **Solution**: We integrated a confirmation dialog. Triggering the global threshold prompts you to apply that threshold to earlier skipped frames.

### 12. Contributor Credits
*   **Files**: `modules/load_tif.py`, `modules/contour_paintbrush.py`, `modules/slice.py`, `web_app/server.py`, `run_web_app.py`, `readme.md`
*   **Problem**: The codebase lacked credits for new contributors.
*   **Solution**: We updated the headers of the files we built or modified to include Abhinav's name, email (`ms24115@iisermohali.ac.in`), and GitHub profile (`https://github.com/sudoax0n`).

### 13. Advanced Morphological Skeletonization & Center-Line Calibration
*   **Files**: `modules/skeleton.py` [NEW], `main.py`
*   **Problem**: Standard contour detection calculates perimeters on raw boundary outlines. Optical diffraction (PSF) and threshold bias distort these outlines. Directly summing grid pixels overestimates curve lengths by 5% to 8% because of digital metrication error.
*   **Solution**: We integrated a 2D morphological skeletonization pipeline. A NetworkX graph-pruning algorithm removes noise branches while keeping the membrane loop topology intact. The Vossepoel & Smeulders statistical chain code formula corrects the digital grid-effect to achieve sub-pixel perimeter accuracy. A toggle switch and a noise filter slider configure parameters at startup, and the GUI overlays the pruned centerline.

---

## Local Web Application

We built a browser-based local application using FastAPI and HTML5 to replace the Matplotlib and EasyGUI interfaces.

### 1. Application Launcher
*   **Files**: `run_web_app.py`
*   **Problem**: Setting up the server required multiple command-line installation steps.
*   **Solution**: We created a launcher script that checks for python dependencies (`fastapi`, `uvicorn`), installs them if missing, and starts the local server.

### 2. FastAPI Backend
*   **Files**: `web_app/server.py`
*   **Problem**: The biophysics algorithms were tied to blocking Tkinter and Matplotlib GUI code.
*   **Solution**: We created a FastAPI backend server that exposes REST endpoints for file uploads, range slicing, cropping, segmentation, and Plotly mesh generation.

### 3. HTML5 Canvas Frontend
*   **Files**: `web_app/templates/index.html`
*   **Problem**: The Matplotlib GUI was slow and lacked user controls.
*   **Solution**: We built a glassmorphic single-page dashboard. You navigate via a progress stepper, select ranges with dual-thumb sliders, crop using HTML5 canvases, and view real-time threshold slider previews.

### 4. Global Thresholding
*   **Files**: `web_app/templates/index.html`, `web_app/server.py`
*   **Problem**: Setting thresholds frame-by-frame was slow.
*   **Solution**: We added a global threshold checkbox. The client sends the threshold to the backend, which calculates circularity-smoothed contours for unvisited frames during mesh generation.

### 5. Original Color Channel Preservation
*   **Files**: `modules/load_tif.py`, `web_app/server.py`
*   **Problem**: The initial grayscale conversion (`convert_to_grayscale_3d`) stripped all color channels to prevent OpenCV crashes. Red fluorescent TRITC/rhodamine microscope images displayed in black and white in the web UI.
*   **Solution**: We modified `load_image_file` to load both a grayscale stack (for processing) and a color stack (for visual rendering). We updated `server.py` to cache both stacks. We corrected BGR/RGB channel swapping in `encode_image_base64` to preserve the original red colors in the browser.

### 6. Segmentation State Isolation
*   **Files**: `web_app/templates/index.html`
*   **Problem**: Manual tracing points leaked across adjacent frames when threshold values were adjusted. Adjusting the global threshold slider wiped custom manual drawings.
*   **Solution**: We added a frame-specific segmentation mode tracker (`STATE.frameSegModes`) to isolate states. We rewrote `loadSegmentFrame()` to lock manually traced boundaries. We configured `updateThreshold()` to clear cached contours only on auto-segmented frames, preserving custom manual drawings during global adjustments.

### 7. Unicode Terminal Compatibility
*   **Files**: `run_web_app.py`
*   **Problem**: Terminal print statements containing unicode emoji characters (such as checkmarks and rockets) crashed Python with a `UnicodeEncodeError` in standard Windows cmd and PowerShell terminals.
*   **Solution**: We replaced unicode emoji characters in terminal print statements with standard ASCII text.

---

## Git Configuration and Branch Merging

### 1. Git Environment and Branch Sync
*   **Files**: `.gitignore` [NEW], git repository configuration
*   **Problem**: Local and remote origin branches diverged, blocking updates. The repository also tracked temporary files (`bugs folder/` and `.venv/`), bloating the repository.
*   **Solution**: We created a `.gitignore` file to ignore Python caches (`__pycache__/`, `*.pyc`), environments (`.venv/`), temporary uploads (`temp_uploads/`), and IDE configurations (`.vscode/`). We concluded the git merge and pushed all commits to origin/main.
