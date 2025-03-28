import bpy
import socket
import threading
import time
import json
import traceback

class CommandExecutor:
    """Class to handle execution of commands received via socket"""
    
    @staticmethod
    def create_cube(params=None):
        """Create a cube with optional parameters"""
        params = params or {}
        location = params.get("location", (0, 0, 0))
        size = params.get("size", 2.0)
        
        # in the main thread since we're modifying the scene
        def _create_cube():
            bpy.ops.mesh.primitive_cube_add(size=size, location=location)
            return "Cube created"
        
        return _create_cube
    
    @staticmethod
    def create_sphere(params=None):
        """Create a sphere with optional parameters"""
        params = params or {}
        location = params.get("location", (0, 0, 0))
        radius = params.get("radius", 1.0)
        
        def _create_sphere():
            bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
            return "Sphere created"
        
        return _create_sphere
    
    @staticmethod
    def delete_all(params=None):
        """Delete all objects in the scene"""
        def _delete_all():
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            return "All objects deleted"
        
        return _delete_all
    
    @staticmethod
    def execute_code(params=None):
        """Execute arbitrary Python code"""
        params = params or {}
        code = params.get("code", "")
        
        def _execute_code():
            try:
                # local namespace for the code execution
                local_namespace = {"bpy": bpy}
                exec(code, {"__builtins__": __builtins__}, local_namespace)
                return f"Code executed successfully"
            except Exception as e:
                error_msg = traceback.format_exc()
                return f"Error executing code: {error_msg}"
        
        return _execute_code
    
    @staticmethod
    def render_scene(params=None):
        """Render the current scene and save to file"""
        params = params or {}
        filepath = params.get("filepath", "//render.png")
        
        def _render_scene():
            original_path = bpy.context.scene.render.filepath
            bpy.context.scene.render.filepath = filepath
            bpy.ops.render.render(write_still=True)
            bpy.context.scene.render.filepath = original_path
            return f"Scene rendered to {filepath}"
        
        return _render_scene


class SocketReceiver(bpy.types.Operator):
    bl_idname = "wm.socket_command_receiver"
    bl_label = "Socket Command Receiver"
    
    _timer = None
    _thread = None
    _socket = None
    _running = False
    _messages = []
    _commands = []
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            # execute any pending commands in the main thread
            commands = self.get_commands()
            for cmd_func, cmd_name in commands:
                try:
                    result = cmd_func()
                    self.report({'INFO'}, f"Command '{cmd_name}' executed: {result}")
                except Exception as e:
                    self.report({'ERROR'}, f"Error executing '{cmd_name}': {str(e)}")
            
            # process received messages
            messages = self.get_messages()
            for message in messages:
                print(f"Received: {message}")
                self.process_command(message)
        
        # Check if we should stop
        if not self._running:
            self.cancel(context)
            return {'CANCELLED'}
            
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        # socket in a separate thread
        self._running = True
        self._thread = threading.Thread(target=self.socket_thread)
        self._thread.daemon = True
        self._thread.start()
        
        # timer to check for messages
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        # clean up
        if self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
        
        self._running = False
        
        if self._socket:
            self._socket.close()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
    
    def socket_thread(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(('localhost', 9999))
            self._socket.listen(1)
            
            print("Command receiver listening on localhost:9999")
            
            while self._running:
                try:
                    # accept connection with a timeout to allow checking _running
                    self._socket.settimeout(1.0)
                    conn, addr = self._socket.accept()
                    self._socket.settimeout(None)
                    
                    print(f"Connection from {addr}")
                    
                    self.handle_connection(conn)
                    
                except socket.timeout:
                    # allow checking _running periodically
                    continue
                except Exception as e:
                    print(f"Socket error in accept: {e}")
                    time.sleep(1)  # prevent tight loop when error
                
            print("Socket thread stopping")
            
        except Exception as e:
            print(f"Socket error: {e}")
        finally:
            if self._socket:
                self._socket.close()
            self._running = False
    
    def handle_connection(self, conn):
        """Handle a single connection"""
        try:
            while self._running:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    
                    message = data.decode('utf-8')
                    self._messages.append(message)
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    break
                    
            conn.close()
            
        except Exception as e:
            print(f"Connection handling error: {e}")
    
    def get_messages(self):
        """Get and clear pending messages"""
        messages = self._messages.copy()
        self._messages.clear()
        return messages
    
    def get_commands(self):
        """Get and clear pending commands"""
        commands = self._commands.copy()
        self._commands.clear()
        return commands
    
    def process_command(self, message):
        """Process a command message"""
        try:
            # parse JSON
            cmd_data = json.loads(message)
            cmd_name = cmd_data.get("command", "")
            params = cmd_data.get("params", {})
            
            # get the command function
            cmd_func = self.get_command_function(cmd_name, params)
            if cmd_func:
                # queue the command for execution (in main thread)
                self._commands.append((cmd_func, cmd_name))
                print(f"Command '{cmd_name}' queued for execution")
            else:
                print(f"Unknown command: {cmd_name}")
                
        except json.JSONDecodeError:
            print(f"Invalid JSON message: {message}")
        except Exception as e:
            print(f"Error processing command: {e}")
    
    def get_command_function(self, cmd_name, params):
        """Get the function to execute for a given command"""
        # map command names to their implementation functions
        command_map = {
            "create_cube": CommandExecutor.create_cube,
            "create_sphere": CommandExecutor.create_sphere,
            "delete_all": CommandExecutor.delete_all,
            "execute_code": CommandExecutor.execute_code,
            "render_scene": CommandExecutor.render_scene,
        }
        
        cmd_creator = command_map.get(cmd_name)
        if cmd_creator:
            return cmd_creator(params)
        
        return None


# panel to start/stop the receiver
class SocketCommandPanel(bpy.types.Panel):
    bl_label = "Socket Command Receiver"
    bl_idname = "VIEW3D_PT_socket_command"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Socket'
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("wm.socket_command_receiver", text="Start Command Receiver")


# register and unregister functions
def register():
    bpy.utils.register_class(SocketReceiver)
    bpy.utils.register_class(SocketCommandPanel)

def unregister():
    bpy.utils.unregister_class(SocketCommandPanel)
    bpy.utils.unregister_class(SocketReceiver)

if __name__ == "__main__":
    register()