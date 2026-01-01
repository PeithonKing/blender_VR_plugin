# **Strategic Handover: Human-in-the-Loop Batch Processing in Blender**

Date: December 29, 2025  
Context: Technical roadmap for building a custom batch-processing tool for 200+ parts.  
Target Audience: Python Developers / AI Assistants.

## **1\. Project Goal & Constraints**

**Objective:** Automate the processing of 200+ unique, organic 3D parts (STLs) where **linear automation is impossible** due to the need for manual human judgment (alignment, positioning, or visual verification) at specific stages.

**Constraints:**

* **Hardware:** Mid-range Laptop (Intel i5, 8GB RAM, Linux).  
* **Workflow:** "Human-in-the-Loop." The script must do the heavy lifting but **pause** execution to allow user interaction in the viewport, then resume.  
* **Selected Tool:** **Blender** (via Python API bpy).

**Why Blender?**

* **OpenSCAD** rejected: Cannot handle organic surface conformance (Minkowski offset is too slow).  
* **FreeCAD** rejected: converting Mesh to B-Rep is too computationally expensive for this volume.  
* **Blender** selected: Native mesh handling, "Shrinkwrap" modifier is instant, and the UI allows for custom interactive panels.

## **2\. The Architectural Pattern: "The Wizard Panel"**

Standard Python scripts run linearly from start to finish. This fails here because we need to pause for human input (moving an object).

The Solution:  
Do not write a single script. Build a State Machine inside a custom UI Panel (N-Panel).

### **The Conceptual Flow**

1. **State Management:** You need a way to store the current iteration number (e.g., "Part 5 of 200") that persists even when the script stops running.  
2. **Atomic Steps:** Break the workflow into discrete "Buttons." Each button performs a specific chunk of work and then **terminates**.  
3. **The Pause:** When a button's action finishes, Blender automatically returns control to the user. This is your "Pause." The user can now freely rotate, scale, or move objects in the 3D viewport.  
4. **Resume:** The user clicks the *next* button, which triggers the next chunk of code to read the current state of the scene (including user edits) and continue.

## **3\. Study Guide: The Blender API Vocabulary**

To build this, you need to research and understand the following specific areas of the Blender API (bpy). Do not look for general tutorials; search for these specific terms.

### **A. For Persistence (The Memory)**

* **Concept:** Storing variables inside the Blender Scene so they survive between button clicks.  
* **Vocabulary to Search:**  
  * bpy.types.PropertyGroup: The class used to define a group of custom variables.  
  * bpy.props.IntProperty: The specific type to store your "Current Index" counter.  
  * PointerProperty: How you attach your custom group to the global Scene.

### **B. For Action (The Logic)**

* **Concept:** Creating the actual functions that run when a button is clicked.  
* **Vocabulary to Search:**  
  * bpy.types.Operator: The base class for all tools/actions.  
  * execute(self, context): The specific method where your geometry code lives.  
  * bl\_idname: The internal name you give your tool so other tools can call it.

### **C. For Interface (The GUI)**

* **Concept:** creating a visual panel in the sidebar to hold your buttons.  
* **Vocabulary to Search:**  
  * bpy.types.Panel: The base class for UI elements.  
  * bl\_region\_type \= 'UI': The setting that places your panel in the side "N-Panel".  
  * layout.operator(): The command to turn your "Operator" (from section B) into a clickable button.

### **D. For Geometry (The Math)**

* **Concept:** Editing meshes non-destructively using the Modifier stack (faster/safer than raw editing).  
* **Vocabulary to Search:**  
  * modifiers.new(): How to add a modifier via code.  
  * type='BOOLEAN': For cutting shapes. **Crucial:** Look up the solver='FAST' option to prevent freezing.  
  * type='SHRINKWRAP': For conforming logos/patterns to organic surfaces. Look up wrap\_method='PROJECT'.  
  * bpy.ops.object.modifier\_apply(): The command to "bake" the result before export.

### **E. For Context (The Selection)**

* **Concept:** Telling Blender *which* object you want to apply the math to.  
* **Vocabulary to Search:**  
  * bpy.context.view\_layer.objects.active: The "Main" object (Gold outline). Modifiers are applied here.  
  * obj.select\_set(True): How to select an object via code.  
  * bpy.ops.object.select\_all(action='DESELECT'): Essential to run before selecting a new target to avoid errors.

## **4\. The Logic Flow Diagram**

This is the abstract logic you need to implement.

**Step 1: Setup Operator**

* **Input:** Reads the "Current Index" from State.  
* **Action:**  
  * Clears the scene (deletes old objects).  
  * Imports the STL corresponding to the Index.  
  * Creates/Imports the "Helper Object" (e.g., the Cube for cutting).  
* **Outcome:** Script ends. User is left with the STL and Cube in the viewport to perform manual alignment.

**Step 2: Processing Operator**

* **Input:** Reads the current positions of objects (accepting the user's manual alignment).  
* **Action:**  
  * Applies the Boolean difference (Face minus Cube).  
  * Imports the Logo/DXF.  
* **Outcome:** Script ends. User is left with the Cut Face and the Logo to perform manual logo positioning.

**Step 3: Completion Operator**

* **Input:** Reads the aligned Logo position.  
* **Action:**  
  * Applies Shrinkwrap (wraps logo onto face).  
  * Exports the final STL.  
  * Increments the "Current Index" counter by \+1.  
  * **Loop:** Triggers "Step 1" automatically to load the next file.  
* **Outcome:** The next part is loaded and ready for the user.