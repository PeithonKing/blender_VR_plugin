import bpy

class FACEGASKET_PT_main_panel(bpy.types.Panel):
    """Main Wizard Panel"""
    bl_label = "Face Gasket Wizard"
    bl_idname = "FACEGASKET_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Face Gasket"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.face_gasket_props

        # Header: Current Step Status
        box = layout.box()
        box.label(text=f"Step: {props.step}", icon='CHECKMARK')

        if props.step == 'START':
            self.draw_start_step(layout, props)
        elif props.step == 'ALIGN':
            self.draw_align_step(layout, props)
        elif props.step == 'PROCESS':
            layout.label(text="Processing Step (Coming Soon)")
        elif props.step == 'FINISH':
            layout.label(text="Finalize Step (Coming Soon)")

        if props.step != 'START':
            layout.separator()
            layout.operator("facegasket.reset_wizard", text="Cancel / Start Over", icon='X')

    def draw_start_step(self, layout, props):
        col = layout.column(align=True)
        col.label(text="1. Select Face Scan (.stl):")
        col.prop(props, "face_mesh_path", text="")
        
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.5
        if props.face_mesh_path:
            row.operator("facegasket.start_wizard", text="Start Wizard", icon='PLAY')
        else:
            row.label(text="Please select a file to continue", icon='INFO')

    def draw_align_step(self, layout, props):
        col = layout.column()
        col.label(text="Instructions:", icon='INFO')
        col.label(text="- Clean the STL (remove noise/artifacts)")
        col.label(text="- Align Mesh to face Positive Y Axis (+Y)")
        col.label(text="- Ensure Mesh is centered")
        
        col.separator()
        col.label(text="Select Gasket Type:")
        col.prop(props, "face_width", text="")
        
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator("facegasket.confirm_alignment", text="Next", icon='CHECKBOX_HLT')
