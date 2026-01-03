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

        # Boolean Operation Temporarily Skipped as per "just import" request
        # face_obj = context.scene.objects.get("FaceMesh")
        # if face_obj:
        #     mod = face_obj.modifiers.new(name="GasketCut", type='BOOLEAN')
        #     # ...
        
        self.report({'INFO'}, f"Gasket Type '{props.face_width}' Imported & Aligned.")
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

