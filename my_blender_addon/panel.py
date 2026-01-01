import bpy

class FACEGASKET_PT_main_panel(bpy.types.Panel):
    """Main Wizard Panel"""
    bl_label = "Face Gasket Wizard"
    bl_idname = "FACEGASKET_PT_main_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

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
        col.label(text="- Move/Rotate the 'Helper Spline'")
        col.label(text="- Align it with the Face mesh")
        
        layout.separator()
        
        row = layout.row()
        row.scale_y = 1.5
        row.operator("facegasket.confirm_alignment", text="Confirm Alignment", icon='CHECKBOX_HLT')
