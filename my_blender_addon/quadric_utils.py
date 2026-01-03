"""
Quadric Surface Utilities

Provides functions to:
1. Fit a general quadric surface to 3D points
2. Solve the quadric equation for y given (x, z)
3. Build a Blender mesh from the quadric
"""

import numpy as np


def fit_quadric(points):
    """
    Fit a general quadric surface to a set of 3D points.
    
    Quadric equation:
        Ax² + By² + Cz² + Dxy + Eyz + Fxz + Gx + Hy + Iz + J = 0
    
    Uses SVD to find the null space of the design matrix.
    
    Args:
        points: numpy array of shape (N, 3)
    
    Returns:
        coeffs: numpy array [A, B, C, D, E, F, G, H, I, J]
    """
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    
    # Build design matrix: each row is [x², y², z², xy, yz, xz, x, y, z, 1]
    M = np.column_stack([
        x**2, y**2, z**2,
        x*y, y*z, x*z,
        x, y, z,
        np.ones_like(x)
    ])
    
    # SVD: find the null space (smallest singular value)
    _, _, Vt = np.linalg.svd(M)
    coeffs = Vt[-1]  # Last row corresponds to smallest singular value
    
    return coeffs


def solve_for_y(coeffs, x, z):
    """
    Solve the quadric equation for y given x and z.
    
    Rearranged: By² + (Dx + Ez + H)y + (Ax² + Cz² + Fxz + Gx + Iz + J) = 0
    
    Args:
        coeffs: [A, B, C, D, E, F, G, H, I, J]
        x, z: scalar or numpy arrays
    
    Returns:
        y1, y2: two solutions (may be NaN if discriminant < 0)
    """
    A, B, C, D, E, F, G, H, I, J = coeffs
    
    # Quadratic coefficients for y
    a = B
    b = D*x + E*z + H
    c = A*x**2 + C*z**2 + F*x*z + G*x + I*z + J
    
    # Discriminant
    disc = b**2 - 4*a*c
    
    # Solutions (NaN where disc < 0)
    sqrt_disc = np.sqrt(np.maximum(disc, 0))
    sqrt_disc = np.where(disc >= 0, sqrt_disc, np.nan)
    
    if np.abs(a) < 1e-10:
        # Linear case: By + c = 0 → y = -c/b
        y1 = -c / (b + 1e-10)
        y2 = y1
    else:
        y1 = (-b + sqrt_disc) / (2*a)
        y2 = (-b - sqrt_disc) / (2*a)
    
    return y1, y2


def build_quadric_mesh(coeffs, xlim, zlim, ylim, resolution=50):
    """
    Build vertices and faces for a quadric surface mesh.
    
    Args:
        coeffs: [A, B, C, D, E, F, G, H, I, J]
        xlim: (xmin, xmax)
        zlim: (zmin, zmax)
        ylim: (ymin, ymax) - solutions outside are discarded
        resolution: grid resolution
    
    Returns:
        vertices: list of (x, y, z) tuples
        faces: list of (i, j, k) triangle indices
    """
    x_vals = np.linspace(xlim[0], xlim[1], resolution)
    z_vals = np.linspace(zlim[0], zlim[1], resolution)
    
    X, Z = np.meshgrid(x_vals, z_vals)
    Y1, Y2 = solve_for_y(coeffs, X, Z)
    
    vertices = []
    vertex_indices = {}  # (i, j, sheet) -> vertex index
    
    def add_vertex(i, j, y_val, sheet):
        """Add vertex if y is valid and in range."""
        if np.isnan(y_val) or y_val < ylim[0] or y_val > ylim[1]:
            return -1
        
        key = (i, j, sheet)
        if key not in vertex_indices:
            vertex_indices[key] = len(vertices)
            vertices.append((X[i, j], y_val, Z[i, j]))
        return vertex_indices[key]
    
    faces = []
    
    # Build faces for each sheet
    for sheet, Y in enumerate([Y1, Y2]):
        for i in range(resolution - 1):
            for j in range(resolution - 1):
                # Get vertex indices for the quad
                v00 = add_vertex(i, j, Y[i, j], sheet)
                v01 = add_vertex(i, j+1, Y[i, j+1], sheet)
                v10 = add_vertex(i+1, j, Y[i+1, j], sheet)
                v11 = add_vertex(i+1, j+1, Y[i+1, j+1], sheet)
                
                # Create triangles only if all vertices are valid
                if v00 >= 0 and v01 >= 0 and v10 >= 0:
                    faces.append((v00, v01, v10))
                if v01 >= 0 and v11 >= 0 and v10 >= 0:
                    faces.append((v01, v11, v10))
    
    return vertices, faces


def create_blender_mesh(name, vertices, faces):
    """
    Create a Blender mesh object from vertices and faces.
    
    Args:
        name: object name
        vertices: list of (x, y, z) tuples
        faces: list of triangle index tuples
    
    Returns:
        The created Blender object
    """
    import bpy
    
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    return obj
