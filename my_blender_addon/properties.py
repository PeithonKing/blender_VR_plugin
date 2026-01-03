import bpy

class FaceGasketProperties(bpy.types.PropertyGroup):
    """Properties for the Face Gasket Wizard"""
    
    # State Enum to track where we are in the wizard
    step: bpy.props.EnumProperty(
        name="Wizard Step",
        description="Current step in the wizard workflow",
        items=[
            ('START', "Start", "Select file and begin"),
            ('ALIGN', "Align", "Align helper mesh"),
            ('PROCESS', "Process", "Cut and place logo"),
            ('FINISH', "Finish", "Finalize and export"),
        ],
        default='START'
    )
    
    # Path to the face mesh STL selected by the user
    face_width: bpy.props.EnumProperty(
        name="Gasket Type",
        description="Select the type of gasket",
        items=[
            ('DEFAULT', "Default", "Standard Gasket Type"),
            ('WIDE', "Wide", "Wide Gasket Type"),
        ],
        default='DEFAULT'
    )
    
    # Internal usage: Store reference names if needed, or just rely on active object
    # For now, we trust the state machine context.
    face_mesh_path: bpy.props.StringProperty(
        name="Face Mesh",
        description="Path to the user's face scan STL",
        subtype='FILE_PATH'
    )
    
    # Internal usage: Store reference names if needed, or just rely on active object
    # For now, we trust the state machine context.
