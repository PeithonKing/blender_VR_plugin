import math
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
        
        # 3. Create Helper Spline (Closed Loop, Y=100 plane)
        # Rotating 90deg on X to make it stand up in the XZ plane
        bpy.ops.curve.primitive_bezier_circle_add(
            radius=50, 
            location=(0, 100, 20),
            rotation=(math.pi / 2, 0, 0)
        )
        helper_obj = context.active_object
        helper_obj.name = "HelperSpline"
        
        # Subdivide to get more points (4 * (1+4) = 20 points)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.subdivide(number_cuts=4)
        bpy.ops.object.mode_set(mode='OBJECT')

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
