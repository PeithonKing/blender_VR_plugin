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
        
        # ========== HIDE HELPERS (Disabled for debugging) ==========
        # helpers_col.hide_viewport = True

        # Advance State to PROCESS (Step 4)
        props.step = 'PROCESS'
        
        self.report({'INFO'}, f"Probe vertices saved to {output_path}. ({len(probe_vertices)} points)")
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

