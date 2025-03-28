# Kettle
Server to remotely controlling Blender by executing commands in your blender project

## Features

- Send commands to Blender from an external Python script
- Create basic 3D objects (cubes, spheres) with customizable parameters
- Execute arbitrary Python code in Blender remotely
- Delete all objects in a scene
- Render scenes with custom output paths
- Interactive command-line interface

## Requirements

- Python 3.6+
- Blender 2.80+

## Installation

1. Run `kettleaddon.py` as a Python Script in Blender
2. Run `kettle.py`

## Usage

### As a Module

```python
from kettle import BlenderCommandSender

# Create a sender with default connection to localhost:9999
sender = BlenderCommandSender()

# Create a cube at coordinates (1, 0, 0) with size 2.0
sender.create_cube(location=(1, 0, 0), size=2.0)

# Create a sphere at coordinates (0, 1, 0) with radius 1.5
sender.create_sphere(location=(0, 1, 0), radius=1.5)

# Execute arbitrary Blender Python code
sender.execute_code("bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2))")

# Render the scene
sender.render_scene(filepath="/path/to/output.png")

# Delete all objects
sender.delete_all()

```

### Interactive Mode
Run the script directly to enter interactive mode:

```python
python kettle.py
```

In interactive mode, you can type commands like:

```
create_cube 1 0 0 2
create_sphere 0 1 0 1.5
execute_code bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2))
render_scene /path/to/output.png
delete_all
help
exit
```

## Command Reference
### Basic Commands
`help` - Display help information about available commands
`create_cube [x y z] [size]` - Create a cube at specified position with given size
`create_sphere [x y z] [radius]` - Create a sphere at specified position with given radius
`delete_all` - Delete all objects in the current scene
`render_scene [filepath]` - Render the current scene and save it to the specified path
`exit` - Exit the command sender
### Advanced Commands
`execute_code [python_code]` - Execute arbitrary Python code in Blender

## Example Code Snippet
```python
# Create a monkey (Suzanne)
execute_code bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2))

# Add a red material to the active object
execute_code mat = bpy.data.materials.new("RedMaterial"); mat.diffuse_color = (1, 0, 0, 1); bpy.context.object.data.materials.append(mat)

# Create simple animation
execute_code bpy.context.object.location.keyframe_insert(data_path="location", frame=1); bpy.context.object.location = (5, 0, 0); bpy.context.object.location.keyframe_insert(data_path="location", frame=30)

# Set render resolution
execute_code bpy.context.scene.render.resolution_x = 1920; bpy.context.scene.render.resolution_y = 1080
```

## Protocol Details
Commands are sent as JSON messages with the following structure:

```json
{
    "command": "command_name",
    "params": {
        "param1": value1,
        "param2": value2
    },
    "timestamp": "YYYY-MM-DD HH:MM:SS",
    "user": "username"
}
```