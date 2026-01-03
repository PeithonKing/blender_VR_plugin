import numpy as np
import bpy
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

        # 3. Create Helper Spline from Data
        # Format: [CO_X, CO_Y, CO_Z, HL_X, HL_Y, HL_Z, HR_X, HR_Y, HR_Z]
        data_rows = np.loadtxt("/home/aritra/Documents/temp/vr_face_gasket/python/my_blender_addon/assets/points.csv", delimiter=",")
        data_rows[:, (1, 4, 7)] = 60
        to_replicate = data_rows[1:-1].copy()
        to_replicate[:, [0, 3, 6]] *= -1  # mirror
        original_hl = to_replicate[:, 3:6].copy()  # swap handles
        original_hr = to_replicate[:, 6:9].copy()  # swap handles
        to_replicate[:, 3:6] = original_hr
        to_replicate[:, 6:9] = original_hl
        full_data = np.vstack((data_rows, to_replicate[::-1]))

        # Create Curve Data
        curve_data = bpy.data.curves.new('HelperSpline', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 12
        
        # Create Spline
        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(len(full_data) - 1)
        
        for i, row in enumerate(full_data):
            bp = spline.bezier_points[i]
            bp.co = row[0:3]
            bp.handle_left = row[3:6]
            bp.handle_right = row[6:9]
            bp.handle_left_type = 'FREE'
            bp.handle_right_type = 'FREE'

        spline.use_cyclic_u = True # Close loop
        
        # Create Object
        helper_obj = bpy.data.objects.new("HelperSpline", curve_data)
        context.collection.objects.link(helper_obj)
        context.view_layer.objects.active = helper_obj
        helper_obj.select_set(True)

        # Lock Y coordinate
        helper_obj.lock_location[1] = True

        # 5. Setup Viewport: Orthographic, Looking from +Y
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

        # 4. Advance State
        props.step = 'ALIGN'
        
        self.report({'INFO'}, "Wizard Started: Align the Helper Spline.")
        return {'FINISHED'}

class FACEGASKET_OT_confirm_alignment(bpy.types.Operator):
    """Confirm Alignment and move to next step"""
    bl_idname = "facegasket.confirm_alignment"
    bl_label = "Confirm Alignment"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.face_gasket_props
        self.report({'INFO'}, "Alignment Confirmed.")
        return {'FINISHED'}

class FACEGASKET_OT_reset_wizard(bpy.types.Operator):
    """Reset the wizard to the start and clear scene"""
    bl_idname = "facegasket.reset_wizard"
    bl_label = "Reset Wizard"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.face_gasket_props
        
        # Select all and delete everything
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        props.step = 'START'
        self.report({'INFO'}, "Wizard Reset and Scene Cleared.")
        return {'FINISHED'}

