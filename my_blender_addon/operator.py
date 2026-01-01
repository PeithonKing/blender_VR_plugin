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
        
        if filepath.lower().endswith('.stl'):
            bpy.ops.wm.stl_import(filepath=filepath)
        elif filepath.lower().endswith('.obj'):
            bpy.ops.wm.obj_import(filepath=filepath)
        else:
            self.report({'ERROR'}, "Unsupported file format. Please use STL or OBJ.")
            return {'CANCELLED'}
        
        face_obj = context.selected_objects[0]
        face_obj.name = "FaceMesh"
        
        # 3. Import or Create Helper Spline
        script_dir = os.path.dirname(os.path.realpath(__file__))
        assets_dir = os.path.join(script_dir, "assets")
        template_path = os.path.join(assets_dir, "spline_template.blend")
        
        helper_obj = None
        
        # If a saved template exists, APPEND it
        if os.path.exists(template_path):
            with bpy.data.libraries.load(template_path, link=False) as (data_from, data_to):
                # Search for any object named 'HelperSpline' in the blend file
                if "HelperSpline" in data_from.objects:
                    data_to.objects = ["HelperSpline"]
            
            if data_to.objects:
                helper_obj = data_to.objects[0]
                context.collection.objects.link(helper_obj)
                self.report({'INFO'}, "Loaded saved Spline Template.")
        
        # Fallback: Create generic circle if no template found
        if not helper_obj:
            bpy.ops.curve.primitive_bezier_circle_add(
                radius=50, 
                location=(0, 100, 20),
                rotation=(math.pi / 2, 0, 0)
            )
            helper_obj = context.active_object
            helper_obj.name = "HelperSpline"
            
            # Subdivide to get more points
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.subdivide(number_cuts=4)
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'WARNING'}, "No template found. Created generic circle.")

        # Ensure name and locks
        helper_obj.name = "HelperSpline"
        helper_obj.lock_location[1] = True

        # 5. Setup Viewport
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

        props.step = 'ALIGN'
        return {'FINISHED'}

class FACEGASKET_OT_save_template(bpy.types.Operator):
    """Save the current HelperSpline as the future template"""
    bl_idname = "facegasket.save_template"
    bl_label = "Save Spline as Template"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if "HelperSpline" not in bpy.data.objects:
            self.report({'ERROR'}, "Object 'HelperSpline' not found in scene.")
            return {'CANCELLED'}
        
        obj = bpy.data.objects["HelperSpline"]
        
        # Setup paths
        script_dir = os.path.dirname(os.path.realpath(__file__))
        assets_dir = os.path.join(script_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        template_path = os.path.join(assets_dir, "spline_template.blend")
        
        # Write the object to a library file (.blend)
        data_blocks = {obj}
        bpy.data.libraries.write(template_path, data_blocks, fake_user=True)
        
        self.report({'INFO'}, f"Spline saved to {template_path}")
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
    """Reset the wizard to the start"""
    bl_idname = "facegasket.reset_wizard"
    bl_label = "Reset Wizard"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.face_gasket_props
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        props.step = 'START'
        self.report({'INFO'}, "Wizard Reset.")
        return {'FINISHED'}
