import subprocess
import platform
import psutil
from agents.base import BaseAgent
from tools.base import Tool

class SystemAgent(BaseAgent):
    def __init__(self):
        super().__init__("SystemAgent")
        self.register_tool(Tool("open_application", "Open a system application", self.open_application))
        self.register_tool(Tool("close_application", "Close a system application", self.close_application))
        self.register_tool(Tool("get_system_info", "Get current system CPU, RAM, and Disk metrics", self.get_system_info))
        self.register_tool(Tool("list_processes", "List currently running processes", self.list_processes))
        self.register_tool(Tool("system_command", "Run raw shell command", self.run_command, high_risk=True))
        
    def open_application(self, **kwargs) -> str:
        app_name = kwargs.get("app_name")
        if not app_name:
            raise ValueError("Missing 'app_name' argument")
            
        try:
            # 1. Try finding a Desktop shortcut first (best for Games like Valorant, Steam apps, etc)
            import os, glob
            desktop_dirs = [
                os.path.expanduser("~\\Desktop"),
                os.path.expanduser("~\\OneDrive\\Desktop"),
                "C:\\Users\\Public\\Desktop"
            ]
            for root_dir in desktop_dirs:
                if os.path.exists(root_dir):
                    shortcuts = glob.glob(os.path.join(root_dir, f"*{app_name}*.lnk"))
                    if shortcuts:
                        subprocess.run(f'powershell -Command "Start-Process \'{shortcuts[0]}\'"', shell=True)
                        return f"Opened application via desktop shortcut: {os.path.basename(shortcuts[0])}"

            # 2. Try opening it normally (works for brave, notepad, chrome, etc)
            result = subprocess.run(f'powershell -Command "Start-Process \'{app_name}\' -ErrorAction Stop"', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return f"Opened application: {app_name}"
            
            # 3. Try with a colon protocol (for UWP apps like WhatsApp)
            result = subprocess.run(f'powershell -Command "Start-Process \'{app_name}:\' -ErrorAction Stop"', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return f"Opened application: {app_name}"
                    
            raise Exception(f"Could not find or open '{app_name}'")
        except Exception as e:
            raise Exception(f"Failed to open {app_name}: {e}")
            
    def close_application(self, **kwargs) -> str:
        app_name = kwargs.get("app_name")
        if not app_name:
            raise ValueError("Missing 'app_name' argument")
            
        try:
            # Use taskkill on Windows to forcibly terminate the process tree
            result = subprocess.run(f'taskkill /F /IM {app_name}.exe /T', shell=True, capture_output=True, text=True)
            output = result.stdout.lower() + result.stderr.lower()
            if result.returncode == 0:
                return f"Closed application: {app_name}"
            elif "not found" in output:
                return f"Application '{app_name}' is not currently running."
            else:
                raise Exception(result.stderr or result.stdout)
        except Exception as e:
            raise Exception(f"Failed to close {app_name}: {e}")
        
    def run_command(self, command: str) -> str:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        raise Exception(result.stderr)

    def get_system_info(self, **kwargs) -> str:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.3)
            cpu_count = psutil.cpu_count(logical=True)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            return (
                f"OS: {platform.system()} {platform.release()} ({platform.machine()})\n"
                f"CPU Utilization: {cpu_percent}% across {cpu_count} logical cores\n"
                f"RAM Usage: {mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB ({mem.percent}% used)\n"
                f"Disk C: Usage: {disk.used / (1024**3):.2f} GB / {disk.total / (1024**3):.2f} GB ({disk.percent}% used)"
            )
        except Exception as e:
            raise Exception(f"Failed to fetch system info: {e}")

    def list_processes(self, filter_name: str = "", limit: int = 15, **kwargs) -> str:
        try:
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    name = p.info['name'] or ""
                    if filter_name and filter_name.lower() not in name.lower():
                        continue
                    procs.append((p.info['pid'], name, p.info['memory_percent'] or 0.0))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            procs.sort(key=lambda x: x[2], reverse=True)
            selected = procs[:int(limit)]
            if not selected:
                return f"No running processes found matching '{filter_name}'." if filter_name else "No active processes found."
            lines = [f"PID {pid:<6} | {name:<25} | Mem: {mem:.1f}%" for pid, name, mem in selected]
            return f"Top Running Processes ({len(selected)} shown):\n" + "\n".join(lines)
        except Exception as e:
            raise Exception(f"Failed to list processes: {e}")
