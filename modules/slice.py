# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Modified and extended by Abhinav (GitHub: https://github.com/sudoax0n), Soft Matter Biophysics Lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Abhinav: ms24115@gmail.com or https://github.com/sudoax0n
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import matplotlib.pyplot as plt
from matplotlib.widgets import RangeSlider, Button

def sliceit(img, display_stack=None):
    """
    img           : grayscale (Z, Y, X) uint8 — used for actual slicing & return value
    display_stack : optional color (Z, Y, X, 3) uint8 — used only for visual display.
                    If None, falls back to img (shows grayscale).
    """
    # disp is what we show to the user; img is what we slice and return
    disp = display_stack if display_stack is not None else img

    image = img.copy()
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    fig.subplots_adjust(bottom=0.25)

    axs[0].imshow(disp[0])
    axs[1].imshow(disp[-1])

    # Create the RangeSlider
    slider_ax = fig.add_axes([0.20, 0.1, 0.50, 0.03])
    slider = RangeSlider(slider_ax, "Range", 1, len(img), valstep=1)

    def update(val):
        # The val passed to a callback by the RangeSlider will
        # be a tuple of (min, max)
        axs[0].cla()
        axs[1].cla()
        axs[0].imshow(disp[val[0]-1])
        axs[1].imshow(disp[val[1]-1])

        # Redraw the figure to ensure it updates
        fig.canvas.draw_idle()

    slider.on_changed(update)

    # Add Confirm & Next button
    btn_ax = fig.add_axes([0.75, 0.08, 0.18, 0.06])
    btn_confirm = Button(btn_ax, "Confirm & Next")

    def on_confirm(event):
        plt.close(fig)

    btn_confirm.on_clicked(on_confirm)

    plt.show()
    min = slider.val[0]-1
    max = slider.val[1]

    images = img[min:max]

    return images