# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import importlib
import subprocess
import sys
import threading
try:
    importlib.import_module("tkinter")
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinter"])
    except Exception as e:
        print(f"❌ Failed: tkinter ({e})")
        

import tkinter as tk
from tkinter import ttk

# List of packages to install
packages = [
    "tifffile",
    "numpy",
    "matplotlib",
    "scikit-image",
    "opencv-python",
    "pandas",
    "shapely",
    "scipy",
    "plotly",
    "pillow",
    "alive-progress",
    "easygui",
    "czifile",
    "PyQt5",
    "pyvista",
    "pyvistaqt"
]

def install_packages(progress_var, status_label, root):
    total = len(packages)
    for i, pkg in enumerate(packages, start=1):
        status_label.config(text=f"Installing {pkg}...")
        root.update_idletasks()

        try:
            importlib.import_module(pkg)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            except Exception as e:
                status_label.config(text=f"❌ Failed: {pkg} ({e})")
                return

        # Update progress bar
        progress = int((i / total) * 100)
        progress_var.set(progress)
        root.update_idletasks()

    status_label.config(text="✅ All packages installed successfully!")

def start_installation(progress_var, status_label, root):
    threading.Thread(target=install_packages, args=(progress_var, status_label, root), daemon=True).start()

def setup_package():
    root = tk.Tk()
    root.title("SMBL - Shape analysis | Package Installer")
    root.geometry("400x150")

    tk.Label(root, text="Installing required Python packages...", font=("Arial", 12)).pack(pady=10)

    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=300)
    progress_bar.pack(pady=10)

    status_label = tk.Label(root, text="Waiting to start...", font=("Arial", 10))
    status_label.pack(pady=5)

    # Start installation after GUI loads
    root.after(1000, start_installation, progress_var, status_label, root)

    root.mainloop()
