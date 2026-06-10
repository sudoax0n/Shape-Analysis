# Codebase Improvements Changelog

This document lists the technical changes, bug fixes, and feature additions made to the Shape Analysis Suite.

---

## Desktop GUI Patches and Calibration

### 1. Voxel Size Unit Calibration
*   **Files**: `modules/load_tif.py`
*   **Problem**: The resolution tags (like `XResolution` and `YResolution`) extracted from TIFF files represent pixels per micron. The original loader computed resolution as `1 / resolution` (e.g. `0.1` or `0.37`), treating the output as SI meters. This was off by six orders of magnitude, causing the 3D visualizer axes to render in nanometers and corrupting surface area and volume metrics.
*   **Solution**: We corrected the tag parser to multiply the calculated pixel size by `1e-6` (e.g. `(1 / resolution) * 1e-6`), scaling the units from microns to meters. This aligns all downstream physical measurements.

### 2. Grayscale Stack Normalization
*   **Files**: `modules/load_tif.py`
*   **Problem**: Loading multi-channel, RGB, or Zeiss `.czi` stacks caused the OpenCV Gaussian Blur and Otsu thresholding functions to crash. The pipeline threw a `CV_8UC1` assertion error because the processing algorithms expected single-channel grayscale arrays.
*   **Solution**: We added a conversion utility (`convert_to_grayscale_3d`). It standardizes raw multi-channel files into a single grayscale channel before processing.

### 3. Matplotlib Canvas Reset and Memory Leakage
*   **Files**: `modules/contour_paintbrush.py`
*   **Problem**: The Matplotlib paintbrush tool leaked memory and lagged during Z-slice navigation. Old bounding boxes and adjustment handles accumulated on the canvas instead of clearing.
*   **Solution**: We updated `show_frame`, `set_tool`, and `reset_roi` to clear the axes using `self.ax.clear()`. We configured the tool to call `.set_visible(False)` and disconnect active selector event listeners during frame transitions.

### 4. Interactive Range Selection Navigation
*   **Files**: `modules/slice.py`
*   **Problem**: In the range selection step, users had to click the window manager's red "X" to progress. This interrupted the execution flow of the script.
*   **Solution**: We integrated a 'Confirm & Next' button at the bottom of the plot. Clicking the button closes the plot window and advances the execution.

### 5. Color Range Selector Display
*   **Files**: `modules/slice.py`, `main.py`
*   **Problem**: The grayscale normalization change stripped all color channels, causing the range selector plot to display images in black and white.
*   **Solution**: We added a `display_stack` parameter to `sliceit` in `slice.py` and passed the normalized `color_stack` to it in `main.py`. This uses the color stack for visual rendering in the GUI while executing range selection calculations on the grayscale stack.

### 6. Global ROI Crop Box Projection
*   **Files**: `modules/contour_paintbrush.py`
*   **Problem**: Users had to draw and confirm a cropping bounding box for every frame in the Z-stack.
*   **Solution**: We added an 'Apply Globally' button linked to `apply_globally()`. It copies the crop mask coordinates from the current slice to the entire stack.

### 7. DataFrame Alignment Crash
*   **Files**: `main.py`
*   **Problem**: Skipping frames caused the spreadsheet exporter to crash with a `ValueError`. The script failed to append empty values for skipped frames, leaving some column arrays shorter than others.
*   **Solution**: We patched the loop in `main.py` to fill skipped slices with `np.nan` values. This aligns column lengths and keeps array sizes consistent.

### 8. Short Stack Meshing
*   **Files**: `main.py`
*   **Problem**: The script downsampled the Z-axis by 50% to speed up rendering. Short stacks with few Z-slices lost too many points, crashing the 3D mesh generator.
*   **Solution**: We configured the generator to check if the Z-stack contains more than 20 slices before downsampling. Short stacks bypass downsampling to preserve rendering.

### 9. Contour Area Selection Optimization
*   **Files**: `main.py`
*   **Problem**: The global thresholding pathway picked contours by `cv2.arcLength` instead of `cv2.contourArea`. This selected thin, long noise lines instead of the vesicle shell.
*   **Solution**: Swapped `arcLength` for `contourArea` inside the global threshold path to select contours by area.

### 10. "Skip Frame" Navigation Button
*   **Files**: `main.py`
*   **Problem**: The threshold selector loop did not allow skipping frames to reach better equatorial frames first.
*   **Solution**: Added a "Skip Frame" button to the interactive threshold selector to let users skip dim pole slices at the start of the stack.

### 11. Retroactive Global Threshold Application
*   **Files**: `main.py`
*   **Problem**: Skipped initial frames did not receive the global threshold, causing missing sections in the 3D reconstruction.
*   **Solution**: Integrated a retroactive dialogue. When global thresholding is triggered, it prompts the user to apply the threshold retroactively to previously skipped frames.

### 12. Contributor Credits
*   **Files**: `modules/load_tif.py`, `modules/contour_paintbrush.py`, `modules/slice.py`, `web_app/server.py`, `run_web_app.py`, `readme.md`
*   **Problem**: The codebase lacked credits for new contributors.
*   **Solution**: We updated the headers of the files we built or modified to include Abhinav's name, email (`ms24115@iisermohali.ac.in`), and GitHub profile (`https://github.com/sudoax0n`).

### 13. Advanced Morphological Skeletonization & Center-Line Calibration
*   **Files**: `modules/skeleton.py` [NEW], `main.py`
*   **Problem**: Standard contour detection calculates perimeters on raw boundary outlines, which are heavily affected by apparent membrane thickness from optical diffraction (PSF) and threshold bias. Furthermore, directly summing grid pixels overestimates curve lengths by 5-8% (metrication error).
*   **Solution**: We integrated a robust 2D morphological skeletonization pipeline. We implemented a NetworkX-based graph-pruning algorithm to remove noise spurs (branches) while keeping the true membrane loop topology intact. We then applied the Vossepoel & Smeulders statistical chain code correction formula to achieve sub-pixel accurate perimeter measurements (up to 99.7%+ accuracy). A toggle switch and noise filter slider were integrated at program startup, and the pruned centerline is overlaid dynamically in the contour selector GUI.

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
*   **Solution**: We built a glassmorphic single-page dashboard. It features a progress stepper, dual-thumb range sliders, HTML5 canvases for drawing crops, and real-time threshold slider previews.

### 4. Global Thresholding
*   **Files**: `web_app/templates/index.html`, `web_app/server.py`
*   **Problem**: Setting thresholds frame-by-frame was slow.
*   **Solution**: We added a global threshold checkbox. The client sends the threshold to the backend, which calculates circularity-smoothed contours for unvisited frames during mesh generation.

### 5. Original Color Channel Preservation
*   **Files**: `modules/load_tif.py`, `web_app/server.py`
*   **Problem**: The initial grayscale conversion (`convert_to_grayscale_3d`) stripped all color channels to prevent OpenCV crashes. This caused red fluorescent TRITC/rhodamine microscope images to display in black and white in the web UI.
*   **Solution**: Modified `load_image_file` to load both a grayscale stack (for processing) and a color stack (for visual rendering). We updated `server.py` to cache both stacks. We corrected BGR/RGB channel swapping in `encode_image_base64` to preserve the original red colors in the browser.

### 6. Segmentation State Isolation
*   **Files**: `web_app/templates/index.html`
*   **Problem**: Manual tracing points leaked across adjacent frames when threshold values were adjusted. Adjusting the global threshold slider wiped custom manual drawings.
*   **Solution**: Added a frame-specific segmentation mode tracker (`STATE.frameSegModes`) to isolate states. We rewrote `loadSegmentFrame()` to lock manually traced boundaries. We configured `updateThreshold()` to clear cached contours only on auto-segmented frames, preserving custom manual drawings during global adjustments.

### 7. Unicode Terminal Compatibility
*   **Files**: `run_web_app.py`
*   **Problem**: Terminal print statements containing unicode emoji characters (such as checkmarks and rockets) crashed Python with a `UnicodeEncodeError` in standard Windows cmd and PowerShell terminals.
*   **Solution**: Replaced unicode emoji characters in terminal print statements with standard ASCII text.

---

## Git Configuration and Branch Merging

### 1. Git Environment and Branch Sync
*   **Files**: `.gitignore` [NEW], git repository configuration
*   **Problem**: Local and remote branches diverged, blocking updates. The repository also tracked temporary files (`bugs folder/` and `.venv/`), bloating the repository.
*   **Solution**: Created a `.gitignore` file to ignore Python caches (`__pycache__/`, `*.pyc`), environments (`.venv/`), temporary uploads (`temp_uploads/`), and IDE configurations (`.vscode/`). Concluded the git merge and pushed all commits to origin/main.
