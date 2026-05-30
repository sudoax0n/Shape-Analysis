# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Modified and extended by Abhinav (GitHub: https://github.com/sudoax0n), Soft Matter Biophysics Lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Abhinav: ms24115@gmail.com or https://github.com/sudoax0n
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RectangleSelector, LassoSelector
from matplotlib.path import Path


class ROISelector:
    def __init__(self, image_stack):
        self.image_stack = [img.copy() for img in image_stack]
        self.current_frame = 0
        self.roi_masks = [np.zeros_like(img, dtype=np.uint8) for img in image_stack]

        self.tool = "rect"
        self.selector = None

        # Setup figure
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(right=0.8)  # leave space for buttons
        self.im = self.ax.imshow(self.image_stack[self.current_frame], cmap="gray")
        self.boundary_line, = self.ax.plot([], [], "y-", lw=2)

        # Buttons
        ax_rect = plt.axes([0.82, 0.82, 0.15, 0.06])
        ax_free = plt.axes([0.82, 0.74, 0.15, 0.06])
        ax_tick = plt.axes([0.82, 0.60, 0.15, 0.06])
        ax_global = plt.axes([0.82, 0.52, 0.15, 0.06])
        ax_reset = plt.axes([0.82, 0.38, 0.15, 0.06])
        ax_finish = plt.axes([0.82, 0.26, 0.15, 0.06])

        self.btn_rect = Button(ax_rect, "Rectangle")
        self.btn_free = Button(ax_free, "Freeform")
        self.btn_tick = Button(ax_tick, "✔ Tick")
        self.btn_global = Button(ax_global, "Apply Globally")
        self.btn_reset = Button(ax_reset, "⟳ Reset")
        self.btn_finish = Button(ax_finish, "⏹ Finish")

        self.btn_rect.on_clicked(lambda e: self.set_tool("rect"))
        self.btn_free.on_clicked(lambda e: self.set_tool("freeform"))
        self.btn_tick.on_clicked(lambda e: self.confirm_and_next())
        self.btn_global.on_clicked(lambda e: self.apply_globally())
        self.btn_reset.on_clicked(lambda e: self.reset_roi())
        self.btn_finish.on_clicked(lambda e: self.finish())

        self.set_tool("rect")
        plt.show()

    def set_tool(self, tool):
        self.tool = tool
        # Clear previous selection visuals
        self.boundary_line.set_data([], [])
        if self.selector:
            try:
                self.selector.disconnect_events()
                self.selector.set_visible(False)
                if hasattr(self.selector, 'clear'):
                    self.selector.clear()
            except Exception:
                pass
            self.selector = None

        # Initialize the new selector
        if tool == "rect":
            self.selector = RectangleSelector(
                self.ax, self.on_rect_select,
                useblit=True, button=[1], interactive=True
            )
        elif tool == "freeform":
            self.selector = LassoSelector(self.ax, onselect=self.on_lasso_select)

        print(f"Switched to {tool}")
        self.fig.canvas.draw_idle()

    def on_rect_select(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        mask = np.zeros_like(self.image_stack[self.current_frame], dtype=np.uint8)
        mask[min(y1,y2):max(y1,y2), min(x1,x2):max(x1,x2)] = 255
        self.roi_masks[self.current_frame] = mask
        self.boundary_line.set_data([x1, x1, x2, x2, x1],
                                    [y1, y2, y2, y1, y1])
        self.fig.canvas.draw_idle()

    def on_lasso_select(self, verts):
        path = Path(verts)
        ny, nx = self.image_stack[self.current_frame].shape
        y, x = np.mgrid[:ny, :nx]
        coords = np.column_stack((x.ravel(), y.ravel()))
        mask = path.contains_points(coords).reshape((ny, nx))
        self.roi_masks[self.current_frame] = (mask.astype(np.uint8) * 255)
        xs, ys = zip(*verts)
        self.boundary_line.set_data(xs, ys)
        self.fig.canvas.draw_idle()

    def reset_roi(self):
        self.roi_masks[self.current_frame] = np.zeros_like(
            self.image_stack[self.current_frame], dtype=np.uint8
        )
        self.boundary_line.set_data([], [])
        # Re-initialize tool to clear active drawings
        self.set_tool(self.tool)
        self.fig.canvas.draw_idle()

    def confirm_and_next(self):
        mask = self.roi_masks[self.current_frame]
        if np.any(mask > 0):
            self.image_stack[self.current_frame][mask == 0] = 0
            print(f"✅ ROI applied for frame {self.current_frame}")
        else:
            print("⚠️ No ROI drawn")

        # Move to next frame
        if self.current_frame < len(self.image_stack) - 1:
            self.current_frame += 1
            self.show_frame()
        else:
            print("✅ Last frame reached — use Finish")

    def apply_globally(self):
        mask = self.roi_masks[self.current_frame]
        if np.any(mask > 0):
            for i in range(len(self.image_stack)):
                self.roi_masks[i] = mask.copy()
                self.image_stack[i][mask == 0] = 0
            print(f"✅ ROI applied globally to all {len(self.image_stack)} frames")
            plt.close(self.fig)
        else:
            print("⚠️ No ROI drawn to apply globally")

    def show_frame(self):
        # Completely clear axes to prevent handles and boxes from accumulating
        self.ax.clear()
        self.im = self.ax.imshow(self.image_stack[self.current_frame], cmap="gray")
        self.boundary_line, = self.ax.plot([], [], "y-", lw=2)

        # Remove previous selector
        if self.selector:
            try:
                self.selector.disconnect_events()
                self.selector.set_visible(False)
                if hasattr(self.selector, 'clear'):
                    self.selector.clear()
            except Exception:
                pass
            self.selector = None

        # Re-initialize selector for the cleared axes
        self.set_tool(self.tool)
        self.fig.canvas.draw_idle()

    def finish(self):
        print("Finished — returning processed stack")
        plt.close(self.fig)


def run_gui(image_stack):
    selector = ROISelector(image_stack)
    return selector.image_stack
