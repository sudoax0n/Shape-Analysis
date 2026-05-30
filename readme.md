# Shape Analysis Tools

A Python-based software suite designed for multi-dimensional shape and deflation analysis of biomimetic and plasma membrane vesicles from confocal microscopy Z-stacks.

Developed at the **Soft Matter Biophysics Lab**, Indian Institute of Science Education and Research (IISER) Mohali.

---

## 🔬 Scientific Context & Publications

This software has been utilized and cited in the following peer-reviewed biophysics publications:

1. **"Shape Analysis of Biomimetic and Plasma Membrane Vesicles"**  
   *Chemistry - A European Journal (2024)*  
   [https://doi.org/10.1002/syst.202400052](https://chemistry-europe.onlinelibrary.wiley.com/doi/10.1002/syst.202400052)

2. **"Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy"**  
   *The Journal of Physical Chemistry B (2024)*  
   [https://doi.org/10.1021/acs.jpcb.4c07431](https://pubs.acs.org/doi/full/10.1021/acs.jpcb.4c07431)

---

## ⚡ Core Features

The suite offers two operational modes: a **brand-new local Web Application** and a **classic Desktop GUI**. Both pipelines support:

* **Robust Grayscale Stack Normalization**: Automatically converts multi-channel, RGB/RGBA, or raw microscope files (`.tif`, `.tiff`, `.czi`) into standard Z-stacks.
* **Interactive Z-Range Trimming**: Trim background slices from the top and bottom of the Z-stack to isolate the target vesicle range.
* **Mask Painting / ROI Bounding Boxes**: Easily crop target regions. Supports **Global ROI** (apply a crop box once to the entire stack at once) to avoid repetitive drawing.
* **Human-in-the-Loop Segmentation**: Adjust segmentation threshold intensity values with dynamic feedback, with fallback options to trace manual polygon boundaries directly on the image canvas.
* **Global Thresholding & Backend Contouring**: Automatically computes circularity-smoothed, optimized contours for all unvisited slices using your global settings, making 3D meshing instant.
* **Marching Cubes 3D Reconstruction**: Computes precise 3D surface area and volume metrics using the divergence theorem on surface mesh boundaries.
* **Spreadsheet Metric Exports**: Saves fully calculated 2D/3D metrics directly as a CSV spreadsheet next to your original data files.

---

## 🚀 Getting Started

### 1. Installation
Clone the repository and navigate into the folder:
```bash
git clone https://github.com/sudoax0n/Shape-Analysis.git
cd Shape-Analysis
```

### 2. Install Dependencies
You can install dependencies manually using the requirements file:
```bash
pip install -r requirements.txt
```
*(Alternatively, both applications contain built-in dependency managers that will automatically check and install missing packages on first startup.)*

---

## 💻 Running the Application

### Option A: Local Web Application (Recommended)
This launches a modern, lag-free web interface in your default browser running on a local FastAPI server. It replaces clunky Matplotlib popups with responsive HTML5 canvases and an embedded Plotly 3D visualizer.

To boot the web app, run:
```bash
python run_web_app.py
```
The browser will automatically open to `http://127.0.0.1:8000`.

### Option B: Classic Desktop GUI
To run the original Matplotlib and EasyGUI-based desktop interface, run:
```bash
python main.py
```

---

## 📊 Pipeline Architecture

```
[Microscope Data (.tif, .czi)]
             │
             ▼
 ┌───────────────────────┐
 │  Grayscale Conversion │
 └───────────┬───────────┘
             │
             ▼
 ┌───────────────────────┐
 │ Z-Slice Range Trimming│
 └───────────┬───────────┘
             │
             ▼
 ┌───────────────────────┐
 │   Global ROI Crop     │
 └───────────┬───────────┘
             │
             ▼
 ┌───────────────────────┐
 │ Threshold Segmenter   │ <───> (Interactive Real-Time Preview)
 └───────────┬───────────┘
             │
             ▼
 ┌───────────────────────┐
 │ Marching Cubes 3D Mesh│
 ├───────────────────────┤
 │ • Compute 3D Volume   │ ───> CSV Spreadsheet Export
 │ • Compute Surface Area│ ───> Interactive Plotly Mesh
 └───────────────────────┘
```

---

## 🏷️ Citing this Software

If you use this suite in your research or publications, please cite the code using our Zenodo DOI:

> **DOI**: [https://doi.org/10.5281/zenodo.17104429](https://doi.org/10.5281/zenodo.17104429)

---

## 👥 Contributors & Contact

* **Dr. Tripta Bhatia** (Group Leader, Soft Matter Biophysics Lab)  
  📧 [bsoftmatter@gmail.com](mailto:bsoftmatter@gmail.com)

* **Tanmay Pandey** (Primary Author & Original Creator)  
  📧 [itstanmaypandey@gmail.com](mailto:itstanmaypandey@gmail.com) | [ms22113@iisermohali.ac.in](mailto:ms22113@iisermohali.ac.in)

* **Abhinav** (Contributor / Web Port Developer)  
  📧 [ms24115@gmail.com](mailto:ms24115@gmail.com) | 💻 GitHub: [@sudoax0n](https://github.com/sudoax0n)
