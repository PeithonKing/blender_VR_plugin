bl_info = {
    "name": "VR Face Gasket Wizard",
    "author": "Aritra Mukhopdhyay",
    "version": (0, 0, 2),
    "blender": (5, 0, 0),
    "location": "Properties Editor > Object Properties",
    "description": "Step-by-step wizard for processing face gaskets",
    "category": "Pipeline",
}

import bpy
from . import properties
from . import panel
from . import operators

classes = (
    properties.FaceGasketProperties,
    operators.FACEGASKET_OT_start_wizard,
    operators.FACEGASKET_OT_confirm_alignment,
    operators.FACEGASKET_OT_reset_wizard,
    panel.FACEGASKET_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Attach properties to the Scene
    bpy.types.Scene.face_gasket_props = bpy.props.PointerProperty(type=properties.FaceGasketProperties)

def unregister():
    del bpy.types.Scene.face_gasket_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
