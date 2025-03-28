import bpy
import socket
import threading
import time
import json
import traceback
import datetime

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
    def create_text_block(params=None):
        """Create a new text block in the Text Editor with the provided code"""
        params = params or {}
        code = params.get("code", "")
        name = params.get("name", "")
        execute = params.get("execute", False)
        
        def _create_text_block():
            try:
                # Generate a default name if none provided
                if not name:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    text_name = f"script_{timestamp}.py"
                else:
                    text_name = name
                    
                # Create a new text block
                if text_name in bpy.data.texts:
                    # If text already exists, clear it and reuse
                    text = bpy.data.texts[text_name]
                    text.clear()
                else:
                    # Create new text
                    text = bpy.data.texts.new(text_name)
                
                # Set the content
                text.write(code)
                
                # Make it the active text in the editor
                for area in bpy.context.screen.areas:
                    if area.type == 'TEXT_EDITOR':
                        area.spaces.active.text = text
                        break
                        
                # Save a copy of the execution status to report back
                execution_status = "not requested"
                        
                if execute:
                    # Execute the text block using the proper method
                    # First, try to find a text editor area to use for context
                    override = None
                    for window in bpy.context.window_manager.windows:
                        for area in window.screen.areas:
                            if area.type == 'TEXT_EDITOR':
                                for region in area.regions:
                                    if region.type == 'WINDOW':
                                        override = {
                                            'window': window,
                                            'screen': window.screen,
                                            'area': area,
                                            'region': region,
                                            'space_data': area.spaces.active,
                                            'edit_text': text
                                        }
                                        break
                                if override:
                                    break
                        if override:
                            break
                    
                    # If we found a text editor, use it to execute
                    if override:
                        # Set as active text
                        override['space_data'].text = text
                        # Use the override context to run the script
                        bpy.ops.text.run_script(override)
                        execution_status = "executed with override context"
                    else:
                        # Fallback method: execute the code directly
                        try:
                            namespace = {'__file__': text_name}
                            exec(compile(code, text_name, 'exec'), namespace)
                            execution_status = "executed directly with exec()"
                        except Exception as exec_error:
                            return f"Text block '{text_name}' created but execution failed: {str(exec_error)}"
                    
                    # Print confirmation to system console
                    print(f"Script '{text_name}' {execution_status}")
                    
                    return f"Text block '{text_name}' created and {execution_status}"
                else:
                    return f"Text block '{text_name}' created (execution not requested)"
                    
            except Exception as e:
                error_msg = traceback.format_exc()
                return f"Error creating/executing text block: {error_msg}"
        
        return _create_text_block
    
    @staticmethod
    def execute_text_block(params=None):
        """Execute a text block by name"""
        params = params or {}
        name = params.get("name", "")
        
        def _execute_text_block():
            try:
                if not name or name not in bpy.data.texts:
                    return f"Text block '{name}' not found"
                    
                text = bpy.data.texts[name]
                
                # Try to find a text editor area to use for context
                override = None
                for window in bpy.context.window_manager.windows:
                    for area in window.screen.areas:
                        if area.type == 'TEXT_EDITOR':
                            for region in area.regions:
                                if region.type == 'WINDOW':
                                    override = {
                                        'window': window,
                                        'screen': window.screen,
                                        'area': area,
                                        'region': region,
                                        'space_data': area.spaces.active,
                                        'edit_text': text
                                    }
                                    break
                            if override:
                                break
                    if override:
                        break
                
                # If we found a text editor, use it to execute
                if override:
                    # Set as active text
                    override['space_data'].text = text
                    # Use the override context to run the script
                    bpy.ops.text.run_script(override)
                    return f"Text block '{name}' executed with override context"
                else:
                    # Fallback method: execute the code directly
                    try:
                        namespace = {'__file__': name}
                        exec(compile(text.as_string(), name, 'exec'), namespace)
                        return f"Text block '{name}' executed directly with exec()"
                    except Exception as exec_error:
                        return f"Error executing text block '{name}': {str(exec_error)}"
                    
            except Exception as e:
                error_msg = traceback.format_exc()
                return f"Error executing text block: {error_msg}"
        
        return _execute_text_block
    
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


class SOCKET_OT_RunReceivedScript(bpy.types.Operator):
    bl_idname = "socket.run_received_script"
    bl_label = "Run Received Script"
    bl_description = "Run the currently active script from the socket receiver"
    
    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == 'TEXT_EDITOR' and context.space_data.text
    
    def execute(self, context):
        try:
            text = context.space_data.text
            
            # Ensure the text is saved (if modified)
            if text.is_modified:
                text.write(text.as_string())
            
            # Execute the script
            namespace = {'__file__': text.name}
            exec(compile(text.as_string(), text.name, 'exec'), namespace)
            
            self.report({'INFO'}, f"Script '{text.name}' executed successfully")
            return {'FINISHED'}
        except Exception as e:
            error_msg = str(e)
            self.report({'ERROR'}, f"Error executing script: {error_msg}")
            print(f"Error executing script: {traceback.format_exc()}")
            return {'CANCELLED'}


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
            # Use a larger buffer size for larger commands
            buffer_size = 8192
            data = b''
            
            while self._running:
                chunk = conn.recv(buffer_size)
                if not chunk:
                    # Connection closed by client
                    break
                
                data += chunk
                
                # If we have less than buffer_size, we probably have all the data
                if len(chunk) < buffer_size:
                    break
            
            if data:
                message = data.decode('utf-8')
                self._messages.append(message)
                
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
            
            # Get metadata
            timestamp = cmd_data.get("timestamp", "unknown time")
            user = cmd_data.get("user", "unknown user")
            print(f"Command '{cmd_name}' received from {user} at {timestamp}")
            
            # Get the appropriate command function
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
            "create_text_block": CommandExecutor.create_text_block,
            "execute_text_block": CommandExecutor.execute_text_block,
            "render_scene": CommandExecutor.render_scene,
        }
        
        cmd_creator = command_map.get(cmd_name)
        if cmd_creator:
            return cmd_creator(params)
        
        return None


# Panel to start/stop the receiver
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
        
        # Add a button to execute the current script
        if context.space_data and context.space_data.type == 'TEXT_EDITOR' and context.space_data.text:
            row = layout.row()
            row.operator("socket.run_received_script", text="Run Current Script")


# register and unregister functions
def register():
    bpy.utils.register_class(SocketReceiver)
    bpy.utils.register_class(SOCKET_OT_RunReceivedScript)
    bpy.utils.register_class(SocketCommandPanel)

def unregister():
    bpy.utils.unregister_class(SocketCommandPanel)
    bpy.utils.unregister_class(SOCKET_OT_RunReceivedScript)
    bpy.utils.unregister_class(SocketReceiver)

if __name__ == "__main__":
    register()