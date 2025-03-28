import socket
import json
import time
import datetime

class BlenderCommandSender:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
    
    def send_command(self, command, params=None):
        """Send a command to Blender with optional parameters"""
        if params is None:
            params = {}
            
        # command message
        cmd_msg = {
            "command": command,
            "params": params,
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "user": "ppmpreetham"
        }
        
        # json
        json_msg = json.dumps(cmd_msg)
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            
            s.sendall(json_msg.encode('utf-8'))
            print(f"Sent command: {command} with params: {params}")
            
            s.close()
            return True
            
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    # testing common commands
    def create_cube(self, location=(0, 0, 0), size=2.0):
        return self.send_command("create_cube", {
            "location": location,
            "size": size
        })
    
    def create_sphere(self, location=(0, 0, 0), radius=1.0):
        return self.send_command("create_sphere", {
            "location": location,
            "radius": radius
        })
    
    def delete_all(self):
        return self.send_command("delete_all")
    
    def execute_code(self, code):
        return self.send_command("execute_code", {
            "code": code
        })
    
    def render_scene(self, filepath="//render.png"):
        return self.send_command("render_scene", {
            "filepath": filepath
        })


def display_help():
    """Display help information about available commands"""
    help_text = """
=== Blender Command Sender Help ===

BASIC COMMANDS:
--------------
help
    Display this help information.

create_cube [x y z] [size]
    Create a cube at the specified position with given size.
    Example: create_cube 0 0 0 2
    Default: Position (0,0,0), Size 2.0

create_sphere [x y z] [radius]
    Create a sphere at the specified position with given radius.
    Example: create_sphere 0 0 0 1.5
    Default: Position (0,0,0), Radius 1.0

delete_all
    Delete all objects in the current scene.
    Example: delete_all

render_scene [filepath]
    Render the current scene and save it to the specified path.
    Example: render_scene C:/temp/render.png
    Default: //render.png (relative to the .blend file)

ADVANCED COMMANDS:
----------------
execute_code [python_code]
    Execute arbitrary Python code in Blender.
    Example: execute_code bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2))

EXAMPLE CODE SNIPPETS:
--------------------
- Create a monkey (Suzanne):
  execute_code bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2))

- Add a red material to the active object:
  execute_code mat = bpy.data.materials.new("RedMaterial"); mat.diffuse_color = (1, 0, 0, 1); bpy.context.object.data.materials.append(mat)

- Create simple animation:
  execute_code bpy.context.object.location.keyframe_insert(data_path="location", frame=1); bpy.context.object.location = (5, 0, 0); bpy.context.object.location.keyframe_insert(data_path="location", frame=30)

- Set render resolution:
  execute_code bpy.context.scene.render.resolution_x = 1920; bpy.context.scene.render.resolution_y = 1080

exit
    Exit the command sender.
"""
    print(help_text)


def interactive_mode():
    """Run an interactive command shell"""
    sender = BlenderCommandSender()
    
    print("===== Blender Command Sender =====")
    print("Type 'help' for a list of available commands")
    print("Type 'exit' to quit")
    print(f"Current user: ppmpreetham")
    print(f"Current time (UTC): {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        try:
            cmd_input = input("\nEnter command: ").strip()
            
            if not cmd_input:
                continue
                
            if cmd_input.lower() == 'exit':
                break
                
            if cmd_input.lower() == 'help':
                display_help()
                continue
                
            parts = cmd_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd == "create_cube":
                # parse location, size
                params = args.split()
                location = [0, 0, 0]
                size = 2.0
                
                if len(params) >= 3:
                    location = [float(params[0]), float(params[1]), float(params[2])]
                if len(params) >= 4:
                    size = float(params[3])
                    
                sender.create_cube(location, size)
                
            elif cmd == "create_sphere":
                # parse location, radius
                params = args.split()
                location = [0, 0, 0]
                radius = 1.0
                
                if len(params) >= 3:
                    location = [float(params[0]), float(params[1]), float(params[2])]
                if len(params) >= 4:
                    radius = float(params[3])
                    
                sender.create_sphere(location, radius)
                
            elif cmd == "delete_all":
                sender.delete_all()
                
            elif cmd == "execute_code":
                sender.execute_code(args)
                
            elif cmd == "render_scene":
                filepath = args.strip() if args else "//render.png"
                sender.render_scene(filepath)
                
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for a list of available commands")
                
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    interactive_mode()