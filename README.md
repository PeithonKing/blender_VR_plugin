# VR Face Gasket Wizard

## About
The VR Face Gasket Wizard is a specialized Blender pipeline designed to automate the creation of custom-fitted face gaskets for VR headsets. Rather than relying on generic shapes, this tool uses a "Human-in-the-Loop" approach to combine high-precision face scan data with a mathematical quadric surface approximation. By projecting a probe surface onto a user's unique facial geometry and fitting a quadric equation to the resulting points, the wizard generates a custom-contoured mesh that maintains structural integrity while ensuring a personalized fit.

## Technical Details
The addon is built on the Blender Python API (`bpy`) and leverages NumPy for heavy-duty linear algebra. The core of the system is a state-machine-driven wizard that guides the user through import and alignment before performing a geometric extraction.

The most critical technical component is the quadric surface fitting. The system captures a set of 3D points from a "Probe" object that has been projected onto the face scan via a Shrinkwrap modifier. These points are then used to solve for the coefficients of a general quadric equation:

$$Ax^2 + By^2 + Cz^2 + Dxy + Eyz + Fxz + Gx + Hy + Iz + J = 0$$

To find the coefficients $[A, B, C, D, E, F, G, H, I, J]$, the tool constructs a design matrix $M$ where each row corresponds to a point $(x, y, z)$ in the form:
$$[x^2, y^2, z^2, xy, yz, xz, x, y, z, 1]$$

The system then applies Singular Value Decomposition (SVD) to $M$. The solution is the eigenvector corresponding to the smallest singular value (the last row of $V^T$), which minimizes the squared error of the fit. Finally, the tool solves for $y$ given $x$ and $z$ coordinates to reconstruct a smooth, continuous mesh surface.

## Execution
1. Ensure you have Blender (v5.0 or compatible) and the `numpy` library installed in your Blender Python environment.
2. Install the addon by loading `__init__.py` or the zipped folder via the Blender Preferences > Add-ons menu.
3. Open the 3D Viewport and locate the "Face Gasket" tab in the N-Panel (sidebar).
4. Configure the settings:
   - **Face Mesh**: Select the path to your user face scan (STL or OBJ).
   - **Gasket Type**: Choose between "Default" or "Wide".
5. Click **Start Wizard** and follow the sequential steps:
   - **Align**: Manually position and rotate the imported face scan.
   - **Align Cover**: Move the imported face cover asset to match the facial contours.
   - **Process**: The tool will automatically generate the Probe, perform the quadric fit, and create the `NewFaceMesh`.
6. The final custom-fitted gasket mesh will be generated directly in your scene.