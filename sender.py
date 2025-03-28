import socket
import json
import time
import datetime
import textwrap

class BlenderCommandSender:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.user = "ppmpreetham"
    
    def send_command(self, command, params=None):
        """Send a command to Blender with optional parameters"""
        if params is None:
            params = {}
            
        # command message
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cmd_msg = {
            "command": command,
            "params": params,
            "timestamp": timestamp,
            "user": self.user
        }
        
        # JSON
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
    
    def create_text_block(self, code, name="", execute=False):
        """
        Send code to be created as a text block in Blender's text editor
        
        Args:
            code (str): The Python code to send
            name (str): Optional name for the text block (default: auto-generated)
            execute (bool): Whether to execute the code after creating the text block
        """
        return self.send_command("create_text_block", {
            "code": code,
            "name": name,
            "execute": execute
        })
    
    def execute_text_block(self, name):
        """
        Execute an existing text block in Blender
        
        Args:
            name (str): The name of the text block to execute
        """
        return self.send_command("execute_text_block", {
            "name": name
        })
    
    def send_script(self, script, execute=False, name=""):
        """
        Send a multiline script to Blender's text editor
        This is useful for pasting code directly from an editor
        """

        normalized_script = textwrap.dedent(script)
        return self.create_text_block(normalized_script, name, execute)
    
    def send_script_file(self, file_path, execute=False):
        """
        Send a Python script from a file to Blender's text editor
        """
        try:
            with open(file_path, 'r') as f:
                script_content = f.read()
                
            # Use the filename as the text block name
            import os
            filename = os.path.basename(file_path)
            
            return self.send_script(script_content, execute, filename)
        except Exception as e:
            print(f"Error reading script file: {e}")
            return False
    
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

SCRIPT COMMANDS:
--------------
script
    Enter multiline script mode. The script will be created as a text block in Blender.
    After entering this command, type or paste your script.
    Type 'END_SCRIPT' on a new line when finished.
    
    Options:
    script [execute] [name]
        execute: Add 'execute' to automatically run the script after creating it
        name: Specify a name for the text block
    
    Example: script execute my_script.py

script_file [filepath] [execute]
    Send a Python script from a file to Blender's text editor.
    Add 'execute' to run the script after creating it.
    Example: script_file C:/scripts/my_blender_script.py execute

execute_text_block [name]
    Execute an existing text block in Blender by name.
    Example: execute_text_block my_script.py

DIRECT CODE EXECUTION:
--------------------
execute_code [python_code]
    Execute single-line Python code in Blender directly (not via text editor).
    Example: execute_code bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2))

EXAMPLE CODE SNIPPETS:
--------------------
- Create a monkey (Suzanne):
  execute_code bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 2))

- Geometry Nodes script (use with 'script' command):
  from geometry_script import *
  
  @tree("Cube Tree")
  def cube_tree():
      return ico_sphere()

exit
    Exit the command sender.
"""
    print(help_text)


def interactive_mode():
    """Run an interactive command shell"""
    sender = BlenderCommandSender()
    
    current_time_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    print("===== Blender Command Sender =====")
    print(f"Current Date and Time (UTC): {current_time_utc}")
    print(f"Current User's Login: {sender.user}")
    print("Type 'help' for a list of available commands")
    print("Type 'exit' to quit")
    
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
            
            # Handle script command with arguments
            if cmd_input.lower().startswith('script'):
                parts = cmd_input.split()
                execute = False
                name = ""
                
                # Parse options
                for part in parts[1:]:
                    if part.lower() == 'execute':
                        execute = True
                    elif not name:  # First non-execute part is the name
                        name = part
                
                print("Enter or paste your script. Type 'END_SCRIPT' on a new line when done:")
                script_lines = []
                while True:
                    line = input()
                    if line.strip() == 'END_SCRIPT':
                        break
                    script_lines.append(line)
                
                script = '\n'.join(script_lines)
                sender.send_script(script, execute, name)
                continue
                
            parts = cmd_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd == "create_cube":
                # Parse location and size
                params = args.split()
                location = [0, 0, 0]
                size = 2.0
                
                if len(params) >= 3:
                    location = [float(params[0]), float(params[1]), float(params[2])]
                if len(params) >= 4:
                    size = float(params[3])
                    
                sender.create_cube(location, size)
                
            elif cmd == "create_sphere":
                # Parse location and radius
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
                
            elif cmd == "script_file":
                parts = args.split()
                file_path = parts[0] if parts else ""
                execute = len(parts) > 1 and parts[1].lower() == 'execute'
                
                if file_path:
                    sender.send_script_file(file_path, execute)
                else:
                    print("Please specify a file path")
                    
            elif cmd == "execute_text_block":
                name = args.strip()
                if name:
                    sender.execute_text_block(name)
                else:
                    print("Please specify a text block name")
                
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