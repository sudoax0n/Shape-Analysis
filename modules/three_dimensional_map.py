# The code is written by Tanmay Pandey, for the Soft Matter Biophysic lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Tanmay Pandey: ms22113@iisermohali.ac.in or itstanmaypandey@gmail.com
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import numpy as np
import plotly.graph_objects as go
from skimage import measure

def calculate_surface_area_volume(verts, faces):
    # Get the vertices corresponding to the faces
    triangles = verts[faces]

    # Calculate the vectors for each triangle face
    vec1 = triangles[:, 1] - triangles[:, 0]
    vec2 = triangles[:, 2] - triangles[:, 0]

    # Compute the cross product of the two vectors (for surface area calculation)
    cross_prod = np.cross(vec1, vec2)

    # Surface area is half the magnitude of the cross products of each face
    surface_area = np.sum(np.linalg.norm(cross_prod, axis=1)) / 2.0

    # Volume using the divergence theorem (signed volume of tetrahedrons)
    volume = np.sum(np.einsum('ij,ij->i', triangles[:, 0], cross_prod)) / 6.0

    return surface_area, np.abs(volume)  # Return absolute volume

def plot_3d_shape(image_stack, voxel_size_x, voxel_size_y, voxel_size_z, ifshow=True, ifsave=False, filename=None):
    # Ask the user for the h-value (number of missing slices)
    h_value = 0#int(input("Enter the number of missing slices (h-value): "))

    # Perform marching cubes to obtain 3D vertices and faces
    verts, faces, _, _ = measure.marching_cubes(image_stack, level=0.5, spacing=(voxel_size_z, voxel_size_y, voxel_size_x))

    # If h-value is provided, close the shape
    if h_value > 0:
        shape_depth = verts[:, 2].max() - verts[:, 2].min()
        
        # Create new vertices to fill in the missing slices
        for i in range(h_value):
            new_z = verts[:, 2].max() + (i + 1) * (shape_depth / (h_value + 1))
            new_verts = verts.copy()
            new_verts[:, 2] = new_z
            
            verts = np.vstack((verts, new_verts))
            new_faces = faces + len(new_verts)
            faces = np.vstack((faces, new_faces))

    # Calculate surface area and volume
    surface_area, volume = calculate_surface_area_volume(verts, faces)

    # Create a 3D interactive plot using Plotly
    fig = go.Figure(data=[go.Mesh3d(
        x=verts[:, 0],
        y=verts[:, 1],
        z=verts[:, 2],
        i=faces[:, 0],
        j=faces[:, 1],
        k=faces[:, 2],
        opacity=1,
        color='red'
    )])

    # Set plot limits and labels
    fig.update_layout(
        scene=dict(
            xaxis_title="X (microns)",
            yaxis_title="Y (microns)",
            zaxis_title="Z (microns)",
            xaxis=dict(nticks=4, range=[verts[:, 0].min(), verts[:, 0].max()]),
            yaxis=dict(nticks=4, range=[verts[:, 1].min(), verts[:, 1].max()]),
            zaxis=dict(nticks=4, range=[verts[:, 2].min(), verts[:, 2].max()])
        )
    )

    # Save the plot as an interactive HTML file if ifsave is True
    if ifsave:
        if filename is not None and isinstance(filename, str) and filename.strip():
            fig.write_html(f"{filename}.html")
            print(f"Interactive plot saved as {filename}.html")
        else:
            print("Error: Invalid filename provided for saving the plot.")
    
    # Show the plot if ifshow is True
    if ifshow:
        fig.show()

    return surface_area, volume
