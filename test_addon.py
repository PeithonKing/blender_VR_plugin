import bpy
import os
import sys

# Add current directory to path so we can import the addon
sys.path.append(os.getcwd())

try:
    import my_blender_addon
    print("Module imported successfully.")
except ImportError as e:
    print(f"Failed to import module: {e}")
    sys.exit(1)

# Register the addon manually since we are not installing it via zip
try:
    my_blender_addon.register()
    print("Addon registered successfully.")
except Exception as e:
    print(f"Failed to register addon: {e}")
    sys.exit(1)

# Test the operator
try:
    # Check if 'Monkey' exists (should not)
    if "Suzanne" in bpy.data.objects:
        print("Error: Suzanne object already exists!")
        sys.exit(1)

    # Run the operator
    bpy.ops.myaddon.add_object()

    # Check if 'Suzanne' exists (should now exist)
    if "Suzanne" in bpy.data.objects:
        print("Success: Suzanne object created!")
    else:
        print("Error: Suzanne object NOT created!")
        sys.exit(1)

except Exception as e:
    print(f"Operator execution failed: {e}")
    sys.exit(1)

print("All tests passed.")
