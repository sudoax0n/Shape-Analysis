# The code is written by Abhinav (GitHub: https://github.com/sudoax0n), Soft Matter Biophysics Lab
# Contact:
#   Dr. Tripta Bhatia (Group Leader): bsoftmatter@gmail.com
#   Abhinav: ms24115@iisermohali.ac.in or https://github.com/sudoax0n
# Please cite if using this program:
#       [1] "Shape Analysis of Biomimetic and Plasma Membrane Vesicles" https://doi.org/10.1002/syst.202400052
#       [2] Experimentally Determined Shapes of Plasma Membrane Vesicles, Phosphatidylcholine (PC), and PC-Cholesterol Vesicles: Vesicle Deflation Analysis Using Confocal Microscopy (https://pubs.acs.org/doi/10.1021/acs.jpcb.4c07431)

import numpy as np
import networkx as nx
from skimage.morphology import skeletonize

def generate_skeleton(binary_mask):
    """
    Reduces a 2D binary vesicle mask to a 1-pixel thick topological skeleton.
    The binary_mask must be a boolean numpy array where the vesicle membrane
    is True and the background is False.
    """
    return skeletonize(binary_mask)

def prune_skeleton(skeleton_array, prune_threshold_pix=15):
    """
    Converts a binary skeleton to an undirected graph and iteratively removes 
    terminal spurs shorter than the threshold, preserving the main 
    continuous vesicle loop topology.
    """
    # 1. Get coordinates of the skeleton pixels
    coords = np.column_stack(np.where(skeleton_array))
    if len(coords) == 0:
        return np.zeros_like(skeleton_array, dtype=bool)
    
    # 2. Build the undirected NetworkX graph
    coord_set = set(map(tuple, coords))
    G = nx.Graph()
    G.add_nodes_from(coord_set)
    
    # Define standard 8-connected neighborhood offsets
    neighbors_8 = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for y, x in coords:
        for dy, dx in neighbors_8:
            ny, nx_pt = y + dy, x + dx
            if (ny, nx_pt) in coord_set:
                weight = np.sqrt(dy**2 + dx**2)
                G.add_edge((y, x), (ny, nx_pt), weight=weight)
                
    # 3. Iterative leaf-removal (spur pruning)
    pruning_active = True
    while pruning_active:
        pruning_active = False
        endpoints = [n for n, d in G.degree() if d == 1]
        
        for endpoint in endpoints:
            # Trace the branch until we hit a junction (degree >= 3) or another endpoint
            path = [endpoint]
            curr = endpoint
            prev = None
            
            while True:
                neighbors = list(G.neighbors(curr))
                next_nodes = [n for n in neighbors if n != prev]
                if not next_nodes:
                    break
                next_node = next_nodes[0]
                
                # Stop tracing if the next node is a junction or another endpoint
                if G.degree(next_node) >= 3 or G.degree(next_node) == 1:
                    path.append(next_node)
                    break
                else:
                    path.append(next_node)
                    prev = curr
                    curr = next_node
            
            # Calculate the branch length (sum of edge weights)
            branch_len = 0.0
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                branch_len += G[u][v]['weight']
                
            # If the branch length is under the threshold, prune it
            if branch_len < prune_threshold_pix:
                # Remove all nodes along the branch except the junction itself (if it ended at a junction)
                nodes_to_remove = path[:-1] if G.degree(path[-1]) >= 3 else path
                G.remove_nodes_from(nodes_to_remove)
                pruning_active = True
                break  # Break out to recalculate degrees and endpoints
                
    # 4. Rasterize the pruned graph back to a binary skeleton array
    pruned_skel = np.zeros_like(skeleton_array, dtype=bool)
    for y, x in G.nodes():
        pruned_skel[y, x] = True
    return pruned_skel

def calculate_vs_perimeter(pruned_skeleton, voxel_size_um=1.0):
    """
    Extracts the ordered pixel chain from a continuous pruned skeleton loop
    and calculates the metrication-corrected geometric perimeter to eliminate
    the grid-effect overestimation.
    """
    coords = np.column_stack(np.where(pruned_skeleton))
    if len(coords) == 0:
        return 0.0, 0.0
    
    # 1. Order coordinates to form a continuous 1D spatial chain using nearest-neighbor
    unvisited = set(map(tuple, coords))
    ordered_chain = []
    
    current_pt = tuple(coords[0])
    ordered_chain.append(current_pt)
    unvisited.remove(current_pt)
    
    neighbors_8 = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    while unvisited:
        found_next = False
        for dy, dx in neighbors_8:
            ny, nx_pt = current_pt[0] + dy, current_pt[1] + dx
            if (ny, nx_pt) in unvisited:
                current_pt = (ny, nx_pt)
                ordered_chain.append(current_pt)
                unvisited.remove(current_pt)
                found_next = True
                break
        if not found_next:
            break
            
    ordered_chain = np.array(ordered_chain)
    if len(ordered_chain) < 3:
        return 0.0, 0.0
        
    # 2. Compute vector transitions between consecutive points (enforcing closed loop)
    next_pts = np.roll(ordered_chain, shift=-1, axis=0)
    deltas = next_pts - ordered_chain
    
    # 3. Identify horizontal/vertical (even) vs diagonal (odd) steps
    abs_deltas = np.abs(deltas)
    step_magnitudes = np.sum(abs_deltas, axis=1)
    
    is_even = (step_magnitudes == 1)
    is_odd = (step_magnitudes == 2)
    
    N_even = np.sum(is_even)
    N_odd = np.sum(is_odd)
    
    # 4. Count corners (where the step direction changes)
    prev_deltas = np.roll(deltas, shift=1, axis=0)
    is_corner = np.any(deltas != prev_deltas, axis=1)
    N_corner = np.sum(is_corner)
    
    # 5. Apply Vossepoel & Smeulders statistical formulation
    P_pixels = (N_even * 0.980) + (N_odd * 1.406) - (N_corner * 0.091)
    P_physical = P_pixels * voxel_size_um
    
    # Naive Euclidean perimeter (for comparison / fallback)
    P_naive_pixels = N_even + N_odd * np.sqrt(2)
    P_naive_physical = P_naive_pixels * voxel_size_um
    
    return P_physical, P_naive_physical
