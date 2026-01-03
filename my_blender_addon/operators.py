import math
import bpy
import bmesh
import os

class FACEGASKET_OT_start_wizard(bpy.types.Operator):
    """Import the Face Mesh and Helper Mesh"""
    bl_idname = "facegasket.start_wizard"
    bl_label = "Start Wizard"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.face_gasket_props
        
        # 1. Clear Scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # 2. Import Face Mesh
        filepath = props.face_mesh_path
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"File not found: {filepath}")
            return {'CANCELLED'}
        
        # Blender 5.0 commands
        if filepath.lower().endswith('.stl'):
            bpy.ops.wm.stl_import(filepath=filepath)
        elif filepath.lower().endswith('.obj'):
            bpy.ops.wm.obj_import(filepath=filepath)
        else:
            self.report({'ERROR'}, "Unsupported file format. Please use STL or OBJ.")
            return {'CANCELLED'}
        
        face_obj = context.selected_objects[0]
        face_obj.name = "FaceMesh"

        # 3. Spline Generation REMOVED (User Pivot)
        # We only import the face mesh and setup the scene now.
        
        # 4. Setup Viewport: Orthographic, Looking from +Y
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                if space:
                    space.region_3d.view_perspective = 'ORTHO'
                    space.region_3d.view_distance = 300.0
                    
                    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                    with context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_axis(type='BACK')
                    break

        # 5. Advance State
        props.step = 'ALIGN'
        
        self.report({'INFO'}, "Wizard Started: Face Mesh Imported.")
        return {'FINISHED'}

class FACEGASKET_OT_confirm_alignment(bpy.types.Operator):
    """Confirm Alignment and move to next step"""
    bl_idname = "facegasket.confirm_alignment"
    bl_label = "Next"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.face_gasket_props
        
        # 1. Determine Asset Path
        addon_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(addon_dir, "assets")
        
        filename = "face_cover_v3.stl" if props.face_width == 'DEFAULT' else "face_cover_wide_v2.stl"
        filepath = os.path.join(assets_dir, filename)
        
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"Asset not found: {filepath}")
            return {'CANCELLED'}
            
        # 2. Import Cutter STL
        try:
            bpy.ops.wm.stl_import(filepath=filepath)
            cutter_obj = context.selected_objects[0]
            cutter_obj.name = "face_cover"
            
            # 3. Transform Cutter (User Request)
            # Rotate 80 degrees on X axis
            cutter_obj.rotation_euler = (math.radians(80), 0, 0)
            cutter_obj.location = (0, 50, 30)
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import asset: {str(e)}")
            return {'CANCELLED'}

        # 4. Advance State to ALIGN_COVER (Step 3)
        props.step = 'ALIGN_COVER'
        
        self.report({'INFO'}, f"FaceCover Imported. Please align it with the Face Mesh.")
        return {'FINISHED'}


class FACEGASKET_OT_confirm_facecover(bpy.types.Operator):
    """Confirm FaceCover Alignment and perform surface selection"""
    bl_idname = "facegasket.confirm_facecover"
    bl_label = "Next"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.face_gasket_props
        
        # Get the FaceCover object
        face_cover_obj = context.scene.objects.get("face_cover")
        if not face_cover_obj:
            self.report({'ERROR'}, "FaceCover object not found!")
            return {'CANCELLED'}
        
        # Ensure we're in Object Mode first
        if context.active_object and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Deselect all, then select and activate face_cover
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = face_cover_obj
        face_cover_obj.select_set(True)
        
        # Enter Edit Mode to select faces
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Deselect all first
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Get BMesh
        me = face_cover_obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        
        # Select target face (Index 7204)
        target_idx = 7204
        if target_idx < len(bm.faces):
            bm.faces[target_idx].select = True
            bmesh.update_edit_mesh(me)
            
            # Select linked faces with sharpness/flatness threshold (10 degrees)
            bpy.ops.mesh.faces_select_linked_flat(sharpness=math.radians(10.0))
        else:
            self.report({'WARNING'}, f"Face Index {target_idx} out of range!")
            return {'CANCELLED'}

        # ========== PROBE EXTRACTION ==========
        # Duplicate selected faces and separate into new object
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')
        
        # Exit Edit Mode to work with objects
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Find the newly created Probe object
        # After separate, the new object is selected
        probe_obj = None
        for obj in context.selected_objects:
            if obj != face_cover_obj:
                probe_obj = obj
                break
        
        if not probe_obj:
            self.report({'ERROR'}, "Failed to create Probe object!")
            return {'CANCELLED'}
        
        probe_obj.name = "Probe"
        
        # ========== HELPERS COLLECTION ==========
        helpers_col = bpy.data.collections.get("Helpers")
        if not helpers_col:
            helpers_col = bpy.data.collections.new("Helpers")
            context.scene.collection.children.link(helpers_col)
        
        # Move face_cover and Probe to Helpers
        for obj in [face_cover_obj, probe_obj]:
            # Unlink from current collection(s)
            for col in obj.users_collection:
                col.objects.unlink(obj)
            # Link to Helpers
            helpers_col.objects.link(obj)
        
        # ========== SHRINKWRAP PROJECT ==========
        face_obj = context.scene.objects.get("FaceMesh")
        if not face_obj:
            self.report({'ERROR'}, "FaceMesh object not found!")
            return {'CANCELLED'}
        
        context.view_layer.objects.active = probe_obj
        probe_obj.select_set(True)
        
        sw_mod = probe_obj.modifiers.new(name="ProjectToFace", type='SHRINKWRAP')
        sw_mod.wrap_method = 'PROJECT'
        sw_mod.wrap_mode = 'ON_SURFACE'  # Snap Mode
        sw_mod.use_project_x = False
        sw_mod.use_project_y = False
        sw_mod.use_project_z = False
        # sw_mod.use_negative_direction = False
        # sw_mod.use_positive_direction = True  # Positive Y direction
        sw_mod.target = face_obj
        
        bpy.ops.object.modifier_apply(modifier="ProjectToFace")
        
        # ========== SAVE PROBE VERTICES TO NUMPY ==========
        import numpy as np
        
        # Get world-space vertex coordinates from Probe
        probe_mesh = probe_obj.data
        world_matrix = probe_obj.matrix_world
        
        vertices = []
        for vert in probe_mesh.vertices:
            world_co = world_matrix @ vert.co
            vertices.append([world_co.x, world_co.y, world_co.z])
        
        probe_vertices = np.array(vertices)
        
        # Save to assets directory
        addon_dir = os.path.dirname(__file__)
        output_path = os.path.join(addon_dir, "assets", "probe_vertices.txt")
        np.savetxt(output_path, probe_vertices)
        
        # ========== FIT QUADRIC SURFACE ==========
        from . import quadric_utils
        
        coeffs = quadric_utils.fit_quadric(probe_vertices)
        
        # Save coefficients for debugging
        coeffs_path = os.path.join(addon_dir, "assets", "quadric_coeffs.txt")
        np.savetxt(coeffs_path, coeffs.T)
        
        # ========== BUILD QUADRIC MESH ==========
        # Use bounding box of probe vertices + margin for limits
        margin = 20.0  # PLACEHOLDER: 10mm margin
        
        x_min, x_max = probe_vertices[:, 0].min() - margin, probe_vertices[:, 0].max() + margin
        z_min, z_max = probe_vertices[:, 2].min() - margin, probe_vertices[:, 2].max() + margin
        y_min, y_max = probe_vertices[:, 1].min() - margin, probe_vertices[:, 1].max() + margin
        
        xlim = (x_min, x_max)
        zlim = (z_min, z_max)
        ylim = ( -100, y_max)  # (y_min, y_max)
        resolution = 100  # PLACEHOLDER: grid resolution
        
        vertices, faces = quadric_utils.build_quadric_mesh(coeffs, xlim, zlim, ylim, resolution)
        
        if len(vertices) > 0:
            gasket_obj = quadric_utils.create_blender_mesh("NewFaceMesh", vertices, faces)
            self.report({'INFO'}, f"NewFaceMesh created with {len(vertices)} vertices.")
        else:
            self.report({'WARNING'}, "No valid quadric surface points found!")
            return {'CANCELLED'}
        
        # ========== TEST: Create Two Copies of Selected Surface ==========
        # Get face_cover from Helpers
        face_cover_test = context.scene.objects.get("face_cover")
        if not face_cover_test:
            self.report({'ERROR'}, "face_cover not found for test!")
            return {'CANCELLED'}
        
        # Make face_cover visible and active
        face_cover_test.hide_set(False)
        context.view_layer.objects.active = face_cover_test
        bpy.ops.object.select_all(action='DESELECT')
        face_cover_test.select_set(True)
        
        # Enter Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Select face 7204 + linked
        me = face_cover_test.data
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        
        if target_idx < len(bm.faces):
            bm.faces[target_idx].select = True
            bmesh.update_edit_mesh(me)
            bpy.ops.mesh.faces_select_linked_flat(sharpness=math.radians(10.0))
        
        # Copy 1: Duplicate and separate
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Find Copy 1
        copy_1 = None
        for obj in context.selected_objects:
            if obj != face_cover_test:
                copy_1 = obj
                break
        copy_1.name = "Copy_1"
        
        # Copy 2: Duplicate Copy_1
        bpy.ops.object.select_all(action='DESELECT')
        copy_1.select_set(True)
        context.view_layer.objects.active = copy_1
        bpy.ops.object.duplicate()
        copy_2 = context.active_object
        copy_2.name = "Copy_2"
        
        # Shrinkwrap Copy_2 onto NewFaceMesh
        sw_mod = copy_2.modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')
        sw_mod.wrap_method = 'NEAREST_SURFACEPOINT'
        sw_mod.wrap_mode = 'ON_SURFACE'
        sw_mod.target = gasket_obj  # NewFaceMesh
        sw_mod.offset = 0
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
        
        # Print counts
        print("=" * 50)
        print("TWO COPIES CREATED")
        print("=" * 50)
        print(f"Copy_1: {len(copy_1.data.vertices)} verts, {len(copy_1.data.edges)} edges, {len(copy_1.data.polygons)} faces")
        print(f"Copy_2: {len(copy_2.data.vertices)} verts, {len(copy_2.data.edges)} edges, {len(copy_2.data.polygons)} faces")
        print("=" * 50)
        # ========== CREATE FACES BETWEEN BOUNDARY EDGES ==========
        # Get mesh data from both copies
        mesh_1 = copy_1.data
        mesh_2 = copy_2.data
        
        # Get world matrices
        mat_1 = copy_1.matrix_world
        mat_2 = copy_2.matrix_world
        
        # Build new mesh with both surfaces + bridging faces
        new_verts = []
        new_faces = []
        
        # Add vertices from Copy_1
        for v in mesh_1.vertices:
            world_co = mat_1 @ v.co
            new_verts.append((world_co.x, world_co.y, world_co.z))
        
        # Add vertices from Copy_2 (offset indices by len(mesh_1.vertices))
        offset = len(mesh_1.vertices)
        for v in mesh_2.vertices:
            world_co = mat_2 @ v.co
            new_verts.append((world_co.x, world_co.y, world_co.z))
        
        # Add faces from Copy_1
        for p in mesh_1.polygons:
            new_faces.append(tuple(p.vertices))
        
        # Add faces from Copy_2 (with offset)
        for p in mesh_2.polygons:
            new_faces.append(tuple(v + offset for v in p.vertices))
        
        # Find boundary edges in Copy_1 and create bridging quads
        # Boundary edge = edge with only 1 linked face
        for edge_idx, edge in enumerate(mesh_1.edges):
            # Check if boundary (only 1 linked polygon)
            linked_faces = [p for p in mesh_1.polygons if edge.key[0] in p.vertices and edge.key[1] in p.vertices]
            
            if len(linked_faces) == 1:
                # This is a boundary edge
                v1_idx = edge.vertices[0]
                v2_idx = edge.vertices[1]
                
                # Corresponding edge in Copy_2 (same index)
                edge_2 = mesh_2.edges[edge_idx]
                v3_idx = edge_2.vertices[0] + offset
                v4_idx = edge_2.vertices[1] + offset
                
                # Create quad face (order matters for normals)
                new_faces.append((v1_idx, v2_idx, v4_idx, v3_idx))
        
        # Create the shell mesh
        shell_mesh = bpy.data.meshes.new("GasketShell_mesh")
        shell_mesh.from_pydata(new_verts, [], new_faces)
        shell_mesh.update()
        
        shell_obj = bpy.data.objects.new("GasketShell", shell_mesh)
        bpy.context.collection.objects.link(shell_obj)
        
        print("GasketShell created with edge-by-edge boundary bridging!")
        
        # ========== HIDE HELPERS (Disabled for debugging) ==========
        # helpers_col.hide_viewport = True
        
        # # ========== TEMP: Set FaceMesh to wireframe for visualization ==========
        # if face_obj:
        #     face_obj.display_type = 'WIRE'
        
        # # ========== TEMP: Create debug cube from limits ==========
        # cube_verts = [
        #     (xlim[0], ylim[0], zlim[0]),
        #     (xlim[1], ylim[0], zlim[0]),
        #     (xlim[1], ylim[1], zlim[0]),
        #     (xlim[0], ylim[1], zlim[0]),
        #     (xlim[0], ylim[0], zlim[1]),
        #     (xlim[1], ylim[0], zlim[1]),
        #     (xlim[1], ylim[1], zlim[1]),
        #     (xlim[0], ylim[1], zlim[1]),
        # ]
        # cube_faces = [
        #     (0, 1, 2, 3),  # bottom
        #     (4, 5, 6, 7),  # top
        #     (0, 1, 5, 4),  # front
        #     (2, 3, 7, 6),  # back
        #     (0, 3, 7, 4),  # left
        #     (1, 2, 6, 5),  # right
        # ]
        # cube_mesh = bpy.data.meshes.new("LimitsCube_mesh")
        # cube_mesh.from_pydata(cube_verts, [], cube_faces)
        # cube_mesh.update()
        # cube_obj = bpy.data.objects.new("LimitsCube", cube_mesh)
        # bpy.context.collection.objects.link(cube_obj)
        # cube_obj.display_type = 'WIRE'




        # Advance State to PROCESS (Step 4)
        props.step = 'PROCESS'
        
        self.report({'INFO'}, f"Quadric fitted and mesh created.")
        return {'FINISHED'}

class FACEGASKET_OT_reset_wizard(bpy.types.Operator):
    """Reset the wizard to the start and clear scene"""
    bl_idname = "facegasket.reset_wizard"
    bl_label = "Reset Wizard"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.face_gasket_props
        
        # Switch to Object Mode first (in case we are in Edit Mode)
        if context.active_object and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Select all and delete everything
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        props.step = 'START'
        self.report({'INFO'}, "Wizard Reset and Scene Cleared.")
        return {'FINISHED'}

