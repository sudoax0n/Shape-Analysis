# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

from matplotlib.widgets import Slider
import matplotlib.pyplot as plt
def color_display_tiff_z_planes(tiff_stack):
    """
    Display Z-planes from a TIFF file and allow the user to select one interactively.
    
    Parameters:
    - tiff_stack: 3D numpy array of TIFF slices.
    """
    num_slices = len(tiff_stack)#.shape[0]
    
    # Initialize the plot
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
    z_index = 0  # Start with the first Z-plane
    img_display = ax.imshow(tiff_stack[z_index], cmap="gray")
    ax.set_title(f"Z-Plane: {z_index}/{num_slices}")
    ax.axis("off")
    
    # Add a slider for Z-plane selection
    ax_slider = plt.axes([0.2, 0.1, 0.65, 0.03], facecolor='lightgoldenrodyellow')
    slider = Slider(ax_slider, 'Z-Plane', 1, num_slices, valinit=1, valstep=1)
    
    def update(val):
        """
        Update the displayed Z-plane based on the slider value.
        """
        z_index = int(slider.val) - 1
        img_display.set_data(tiff_stack[z_index])
        ax.set_title(f"Z-Plane: {z_index}/{num_slices}")
        fig.canvas.draw_idle()
    
    slider.on_changed(update)
    plt.show()