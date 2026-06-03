# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

try:
    import numpy as np
    import matplotlib.pyplot as plt
    import cv2
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.widgets import PolygonSelector, Button, Slider
    from shapely.geometry import Polygon as ShapelyPolygon
    import os
    from scipy.ndimage import zoom
    from alive_progress import alive_bar

    import easygui as eg
    import pandas as pd
    from modules.load_tif import load_image_file
    from modules.hist_stretching import histogram_stretching
    from modules.adjust_epsilon import adjust_epsilon_for_circularity
    from modules.align_contour import align_contours
    from modules.contour_paintbrush import run_gui as color_the_stack
    from modules.display_tiff_planes import color_display_tiff_z_planes
    from modules.entropy_threshold import entropy_thresholding
    from modules.min_max import show_min_max_image
    from modules.montage import create_montage
    from modules.polygon import draw_polygon
    from modules.shape_paramters import calculate_shape_parameters
    from modules.slice import sliceit
    from modules.three_dimensional_map import plot_3d_shape
    from mesh_view import nothing
    import webbrowser
    import requests # Used to download the image

except Exception:
    from modules.package_setup import setup_package
    setup_package()
    # after setup, re-importing would normally be done; keeping logic simple here.

# ---------------------------
# Helper: interactive contour selector per frame
# ---------------------------
def select_contour_interactive(image_gray, title="Frame", init_thresh=None):
    """
    Shows a matplotlib window with:
      - image (plasma cmap)
      - threshold slider (updates auto-contour)
      - Manual polygon selector (PolygonSelector)
      - Confirm button (accept and close)
      - Reset button (revert to auto contour)
    Returns:
      contour_pts (Nx2 int numpy array) and userSelect (True if manual polygon used)
    """
    # ensure grayscale uint8
    img = np.asarray(image_gray, dtype=np.uint8)
    ny, nx = img.shape

    # compute initial auto-contour (use Otsu if init_thresh is None)
    def compute_auto_contour(thresh_val):
        # threshold tozero then find contours; fallback to Otsu if not provided
        if thresh_val is None:
            _, t = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_TOZERO)
        else:
            _, t = cv2.threshold(img, int(thresh_val), 255, cv2.THRESH_TOZERO)
        contours, _ = cv2.findContours(t, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        # choose largest by area
        c = max(contours, key=lambda c: cv2.contourArea(c))
        return c[:, 0, :]  # Nx2

    # Attempt to smooth initial contour using adjust_epsilon_for_circularity if available
    # We'll compute a preliminary max_contour with Otsu
    tmp_thresh = None
    initial = compute_auto_contour(init_thresh)
    if initial is None:
        # fallback: binary adaptive or low threshold
        _, t = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(t, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            initial = max(contours, key=lambda c: cv2.contourArea(c))[:, 0, :]

    # If user code provides adjust_epsilon_for_circularity, try smoothing
    try:
        if initial is not None:
            # convert format for adjust_epsilon: expects cv2 contour (Nx1x2)
            tmp_contour = initial.reshape((-1, 1, 2)).astype(np.int32)
            smoothed, _ = adjust_epsilon_for_circularity(tmp_contour, 0.2, 100)
            if smoothed is not None and len(smoothed) > 0:
                initial = smoothed[:, 0, :].astype(np.int32)
    except Exception:
        pass

    # State captured by closures
    current_contour = initial.copy() if initial is not None else None
    manual_used = False
    confirmed = {"val": False}  # mutable closure to detect confirm
    global_applied = {"val": False, "threshold": 127}
    skipped = {"val": False}  # user clicked Skip Frame
    polygon_patch = None

    fig, ax = plt.subplots(figsize=(7, 7))
    plt.subplots_adjust(right=0.75, bottom=0.18)
    ax.set_title(title)
    im_handle = ax.imshow(img, cmap="plasma")
    ax.set_axis_off()

    # metrics axis (small box)
    ax_metrics = fig.add_axes([0.78, 0.1, 0.2, 0.15])
    ax_metrics.axis("off")

    # Buttons & slider axes  (Skip Frame added below Apply Globally)
    ax_btn_confirm = fig.add_axes([0.78, 0.78, 0.18, 0.06])
    ax_btn_reset   = fig.add_axes([0.78, 0.70, 0.18, 0.06])
    ax_btn_manual  = fig.add_axes([0.78, 0.62, 0.18, 0.06])
    ax_btn_global  = fig.add_axes([0.78, 0.54, 0.18, 0.06])
    ax_btn_skip    = fig.add_axes([0.78, 0.46, 0.18, 0.06])
    ax_slider = fig.add_axes([0.15, 0.05, 0.55, 0.04])

    btn_confirm = Button(ax_btn_confirm, "Confirm (→ next)")
    btn_reset   = Button(ax_btn_reset,   "Reset Auto")
    btn_manual  = Button(ax_btn_manual,  "Manual Polygon")
    btn_global  = Button(ax_btn_global,  "Apply Globally")
    btn_skip    = Button(ax_btn_skip,    "Skip Frame", color="#ffcc80", hovercolor="#ffa726")
    slider = Slider(ax_slider, "Threshold", 0, 255, valinit=127, valstep=1)

    # If we have an initial threshold guess, set slider
    if init_thresh is not None:
        slider.set_val(init_thresh)

    # polygon selector variable
    poly_selector = {"obj": None}

    def draw_contour_on_ax(contour_pts):
        nonlocal polygon_patch
        # remove existing patch
        if polygon_patch is not None:
            try:
                polygon_patch.remove()
            except Exception:
                pass
            polygon_patch = None
        if contour_pts is None or len(contour_pts) == 0:
            fig.canvas.draw_idle()
            return
        # ensure closed polygon for display
        pts = np.array(contour_pts)
        if not np.all(pts[0] == pts[-1]):
            pts_plot = np.vstack([pts, pts[0]])
        else:
            pts_plot = pts
        polygon_patch = MplPolygon(pts_plot, closed=True, fill=False, edgecolor="red", linewidth=2)
        ax.add_patch(polygon_patch)
        # compute metrics via shapely
        try:
            shp = ShapelyPolygon(pts)
            area = float(shp.area)
            perim = float(shp.length)
        except Exception:
            area = 0.0
            perim = 0.0
        # update metrics box
        ax_metrics.clear()
        ax_metrics.axis("off")
        ax_metrics.text(0.01, 0.7, f"Area: {area:.2f}", fontsize=10, bbox=dict(facecolor="white", alpha=0.8))
        ax_metrics.text(0.01, 0.25, f"Perimeter: {perim:.2f}", fontsize=10, bbox=dict(facecolor="white", alpha=0.8))
        fig.canvas.draw_idle()

    # initial draw
    draw_contour_on_ax(current_contour)

    # Slider callback: update auto-contour if not in manual mode
    def on_slider(val):
        nonlocal current_contour, manual_used
        if manual_used:
            return  # do not override manual selection until reset
        thresh_val = int(val)
        ct = compute_auto_contour(thresh_val)
        current_contour = ct.copy() if ct is not None else None
        draw_contour_on_ax(current_contour)

    slider.on_changed(on_slider)

    # Manual polygon callback
    def on_manual_polygon(verts):
        # verts is list of (x, y) float points in data coords
        nonlocal current_contour, manual_used
        manual_used = True
        pts = np.array(verts, dtype=np.int32)
        # ensure closed
        if pts.shape[0] >= 3:
            current_contour = pts
        else:
            current_contour = None
        draw_contour_on_ax(current_contour)

    def activate_manual(event):
        # activate polygon selector
        nonlocal poly_selector, manual_used
        manual_used = True
        if poly_selector["obj"] is not None:
            try:
                poly_selector["obj"].disconnect_events()
            except Exception:
                pass
            poly_selector["obj"] = None
        poly_selector["obj"] = PolygonSelector(ax, on_manual_polygon, useblit=True)
        fig.canvas.draw_idle()

    btn_manual.on_clicked(activate_manual)

    # Reset: back to auto mode (use current slider val)
    def on_reset(event):
        nonlocal manual_used, current_contour
        manual_used = False
        current_contour = compute_auto_contour(int(slider.val))
        draw_contour_on_ax(current_contour)

    btn_reset.on_clicked(on_reset)

    # Confirm: close figure and return current polygon
    def on_confirm(event):
        nonlocal confirmed
        confirmed["val"] = True
        plt.close(fig)

    btn_confirm.on_clicked(on_confirm)

    def on_global(event):
        global_applied["val"] = True
        global_applied["threshold"] = int(slider.val)
        confirmed["val"] = True
        plt.close(fig)

    btn_global.on_clicked(on_global)

    def on_skip(event):
        """Skip this frame — no contour saved, loop moves to the next frame."""
        skipped["val"] = True
        confirmed["val"] = True  # close cleanly
        plt.close(fig)

    btn_skip.on_clicked(on_skip)

    # Show window and block until closed (either confirm or user closes manually)
    plt.show()

    # Skipped: return None contour + skipped flag
    if skipped["val"]:
        return None, False, global_applied, True

    # After closing, if confirmed, return contour and flag and global state
    if confirmed["val"] and current_contour is not None:
        contour = np.asarray(current_contour, dtype=np.int32)
        # ensure correct shape for cv2.drawContours: Nx1x2
        if contour.ndim == 2 and contour.shape[0] > 0:
            return contour.reshape((-1, 1, 2)), manual_used, global_applied, False
    # if not confirmed but user closed window, return whatever current contour available and False
    if current_contour is None:
        return None, False, global_applied, False
    return np.asarray(current_contour, dtype=np.int32).reshape((-1, 1, 2)), manual_used, global_applied, False

# ---------------------------
# Main script: iterate over files and frames
# ---------------------------

files = []
dirs = []


def main_welcome_screen():
    # --- Configuration ---
    # Text for the welcome screen
    welcome_text = (
        "Welcome to the Shape Analysis tool\n\n"
        "Developed by the Soft Matter Biophysics Lab at\n"
        "Indian Institute of Science Education and Research (IISER) Mohali."
    )
    
    # Title for the window
    window_title = "Shape Analysis Tool"
    
    # Button options
    choices = ["Continue", "Website", "GitHub", "Contact"]
    
    # URLs and links
    website_url = "http://bhattri.github.io/Biophysics"
    github_url = "https://github.com/tanmay1902/Shape-Analysis"
    contact_mailto = "mailto:itstanmaypandey@gmail.com?cc=bsoftmatter@gmail.com"
    
    # Logo URL and local file name
    # Note: easygui can only display one image. We're using the institute's logo.
    logo_filename = "logo.jpg"

    # --- Logic ---
    # Download the logo
    image_path = logo_filename
    
    # Loop to keep the welcome screen open until user continues or closes
    while True:
        # Display the button box with the image and choices
        user_choice = eg.buttonbox(
            msg=welcome_text,
            title=window_title,
            choices=choices,
            image=image_path  # Path to the downloaded logo
        )

        # Act based on the user's choice
        if user_choice == "Continue":
            print("Proceeding with the application...")
            break  # Exit the loop and continue the program
        
        elif user_choice == "Website":
            webbrowser.open(website_url)
        
        elif user_choice == "GitHub":
            webbrowser.open(github_url)
        
        elif user_choice == "Contact":
            webbrowser.open(contact_mailto)
            
        else:
            # This handles the case where the user closes the window
            print("Application closed by user.")
            break

main_welcome_screen()

dir = eg.diropenbox('Open the parent directory', 'SMBL')
if dir is None:
    raise SystemExit("No directory selected")

dirs = [x[0] for x in os.walk(dir)]
for d in dirs:
    for f in os.listdir(d):
        if f.endswith('.tif') or f.endswith('.tiff') or f.endswith('.czi'):
            files.append(f"{d}/{f}")

if len(files) == 0:
    raise SystemExit("No image files found in the selected directory")

with alive_bar(len(files)) as bar:
    for file in files:
        file_path = file
        # Load image stack and voxel information
        image_stack, color_stack, voxel_size_x, voxel_size_y, voxel_size_z = load_image_file(file_path, return_color=True)
        # Ensure image_stack is (z, y, x) and uint8
        image_stack = np.squeeze(image_stack)
        if image_stack.ndim == 2:
            image_stack = image_stack[np.newaxis, ...]
        image_stack = (image_stack - np.min(image_stack))
        if np.max(image_stack) > 0:
            image_stack = (image_stack / np.max(image_stack) * 255.0).astype(np.uint8)
        else:
            image_stack = image_stack.astype(np.uint8)

        # Normalize the color stack for display (same 0-255 scaling as grayscale)
        if color_stack is not None:
            color_stack = np.asarray(color_stack)
            color_stack = (color_stack - np.min(color_stack))
            if np.max(color_stack) > 0:
                color_stack = (color_stack / np.max(color_stack) * 255.0).astype(np.uint8)
            else:
                color_stack = color_stack.astype(np.uint8)
        else:
            color_stack = None

        print(fr'''
            File Information\n
            Resolution:\n
                X : {voxel_size_x/1e-6} $ \mu $,\n
                Y : {voxel_size_y/1e-6} $ \mu $,\n
                Z : {voxel_size_z/1e-6} $ \mu $,\n  
            ''')

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

        # Preprocessing pipeline (your original call)
        try:
            image_stack = color_the_stack(sliceit(histogram_stretching(image_stack), display_stack=color_stack))
        except Exception:
            # If color_the_stack fails or isn't desired, fallback to preprocessed stack
            image_stack = image_stack

        montage = eg.ynbox("Do you want Image montage?","SMBL - Shape Analysis")
        if montage:
            create_montage(image_stack,voxel_size_x, voxel_size_y, voxel_size_z,save_path=f"{file_path}")
        # Process each frame and use interactive selector
        global_threshold_active = False
        global_threshold_val = 127

        for idx, image in enumerate(image_stack):
            image = np.uint8(image)
            # blur and threshold initial for auto-contour smoothing
            blur = cv2.GaussianBlur(image, (5, 5), 3)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_TOZERO)

            if global_threshold_active:
                _, thresh_global = cv2.threshold(blur, global_threshold_val, 255, cv2.THRESH_TOZERO)
                contours, _ = cv2.findContours(thresh_global, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # If the fixed global threshold finds nothing (e.g. dim pole slices of a vesicle),
                # fall back to Otsu thresholding for this frame rather than silently skipping it.
                if len(contours) == 0:
                    print(f"Frame {idx}: global threshold {global_threshold_val} found no contours — falling back to Otsu.")
                    _, thresh_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_TOZERO)
                    contours, _ = cv2.findContours(thresh_otsu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if len(contours) == 0:
                    contour_pts_cv2 = None
                else:
                    max_contour = max(contours, key=lambda c: cv2.contourArea(c))
                    try:
                        smoothed_contour, _ = adjust_epsilon_for_circularity(max_contour, 0.2, 100)
                    except Exception:
                        smoothed_contour = max_contour
                    contour_pts_cv2 = smoothed_contour
                userSelect = False
            else:
                # Launch interactive selector for this frame, passing the raw image to prevent double drawing the contour
                contour_pts_cv2, userSelect, global_state, frame_skipped = select_contour_interactive(
                    image, title=f"{os.path.basename(file_path)} - frame {idx}", init_thresh=127
                )

                if frame_skipped:
                    print(f"Frame {idx}: skipped by user.")
                    # record zeros and move on — user will apply global from a later frame
                    for k in data.keys():
                        data[k].append(0.0)
                    contour_stack.append(np.zeros_like(thresh))
                    continue

                if global_state is not None and global_state.get("val"):
                    global_threshold_active = True
                    global_threshold_val = global_state.get("threshold", 127)
                    print(f"Global threshold activated: {global_threshold_val}")

            # Initialize metrics for this frame with safe default fallbacks
            frame_metrics = {k: 0.0 for k in data.keys()}
            for k in frame_metrics:
                if k.startswith('Ellipse_'):
                    frame_metrics[k] = np.nan

            if contour_pts_cv2 is not None:
                # compute metrics
                try:
                    contour_pts_arr = contour_pts_cv2.reshape((-1, 2))
                    shapely_polygon = ShapelyPolygon(contour_pts_arr)
                    area = shapely_polygon.area
                    perim = shapely_polygon.length
                    circularity = 4 * np.pi * (area / (perim ** 2)) if perim > 0 else 0
                except Exception:
                    try:
                        area = cv2.contourArea(contour_pts_cv2)
                        perim = cv2.arcLength(contour_pts_cv2, closed=True)
                        circularity = 4 * np.pi * (area / (perim ** 2)) if perim > 0 else 0
                    except Exception:
                        area = 0.0
                        perim = 0.0
                        circularity = 0.0

                print(f"Frame {idx}: Area: {area} | Perimeter: {perim} | Circularity: {circularity:.4f}")

                frame_metrics['area'] = area * (voxel_size_x ** 2)
                frame_metrics['area_pix'] = area
                frame_metrics['perim_pix'] = perim
                frame_metrics['volume'] = area * (voxel_size_x ** 2) * voxel_size_z
                frame_metrics['perimeter'] = perim * voxel_size_x
                frame_metrics['surface_area'] = perim * voxel_size_x * voxel_size_z

                # shape parameters
                try:
                    shape_params = calculate_shape_parameters(contour_pts_cv2, voxel_size_x, voxel_size_y, voxel_size_z)
                    if shape_params:
                        for key, val in shape_params.items():
                            data_key = f"Ellipse_{key}"
                            if data_key in frame_metrics:
                                frame_metrics[data_key] = val
                except Exception:
                    pass

                # Create blank image and draw contour to make mask
                zero_image = np.zeros_like(thresh)
                try:
                    pts_for_draw = contour_pts_cv2
                    if pts_for_draw.ndim == 3 and pts_for_draw.shape[1] == 1:
                        pass
                    elif pts_for_draw.ndim == 2:
                        pts_for_draw = pts_for_draw.reshape((-1, 1, 2))
                    cv2.drawContours(zero_image, [pts_for_draw], -1, (255, 255, 255), thickness=-1)
                except Exception:
                    try:
                        cv2.drawContours(zero_image, [contour_pts_cv2], -1, (255, 255, 255), 2)
                    except Exception:
                        pass
                contour_stack.append(zero_image)
            else:
                print(f"Frame {idx}: no contour selected; skipping.")
                contour_stack.append(np.zeros_like(thresh))

            # ALWAYS append exactly one value to all columns in data to prevent lengths mismatch
            for k in data.keys():
                data[k].append(frame_metrics[k])

        # After all frames processed
        
        # Align contours and create 3D stack
        try:
            contour_stack = align_contours(contour_stack)
        except Exception:
            # if align_contours fails, just stack as-is
            pass

        if len(contour_stack) > 0:
            contour_stack_3d = np.stack(contour_stack, axis=0)
            contour_stack_3d = (contour_stack_3d > 0).astype(np.uint8)
            # downsample for 3D plotting (if desired)
            try:
                # Only downsample Z if stack has enough slices; always downsample XY
                nz = contour_stack_3d.shape[0]
                zoom_z = 0.5 if nz > 20 else 1.0
                downsampled_stack = zoom(contour_stack_3d, (zoom_z, 0.5, 0.5), order=1)
            except Exception:
                downsampled_stack = contour_stack_3d
            # compute 3D surface area and volume
            try:
                surface_3d, vol_3d = plot_3d_shape(downsampled_stack, voxel_size_x, voxel_size_y, voxel_size_z, False, True, file_path)
                data['3D_Surface_Area'] = surface_3d
                data['3D_Volume'] = vol_3d
            except Exception:
                data['3D_Surface_Area'] = np.nan
                data['3D_Volume'] = np.nan
        else:
            data['3D_Surface_Area'] = np.nan
            data['3D_Volume'] = np.nan

        # Save results to CSV
        df = pd.DataFrame(data)
        df.to_csv(f'{file_path}.csv', index=False)
        print(f"Saved results to {file_path}.csv")
    bar()
print("All files processed.")
