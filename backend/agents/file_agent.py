import os
import shutil
from agents.base import BaseAgent
from tools.base import Tool

class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__("FileAgent")
        self.register_tool(Tool("search_file", "Search for a file", self.search_file))
        self.register_tool(Tool("read_file", "Read text content from a file", self.read_file))
        self.register_tool(Tool("write_file", "Write text content to a file", self.write_file))
        self.register_tool(Tool("append_file", "Append text content to a file", self.append_file))
        self.register_tool(Tool("create_file", "Create an empty file", self.create_file))
        self.register_tool(Tool("copy_file", "Copy a file from src to dest", self.copy_file))
        self.register_tool(Tool("move_file", "Move or rename a file", self.move_file))
        self.register_tool(Tool("delete_file", "Delete a file", self.delete_file, high_risk=True))
        self.register_tool(Tool("create_folder", "Create a directory folder", self.create_folder))
        self.register_tool(Tool("list_directory", "List files and folders in a directory", self.list_directory))
        
    def _normalize_path(self, filepath: str) -> str:
        filepath = os.path.expanduser(filepath)
        
        # Replace hallucinated unix home directories with real home directory
        lower_path = filepath.lower()
        if lower_path.startswith('/home/user') or lower_path.startswith('\\home\\user'):
            filepath = os.path.join(os.path.expanduser('~'), filepath[11:])
            lower_path = filepath.lower()
            
        # Handle 'desktop' prefix from LLM
        if lower_path.startswith('desktop\\') or lower_path.startswith('desktop/'):
            filepath = os.path.join(os.path.expanduser('~'), 'Desktop', filepath[8:])
        elif lower_path == 'desktop':
            filepath = os.path.expanduser('~/Desktop')
            
        filepath = os.path.normpath(filepath)
        
        # Handle Windows OneDrive Desktop Sync
        desktop_path = os.path.normpath(os.path.expanduser("~/Desktop"))
        onedrive_desktop = os.path.normpath(os.path.expanduser("~/OneDrive/Desktop"))
        
        if filepath.startswith(desktop_path):
            onedrive_filepath = filepath.replace(desktop_path, onedrive_desktop, 1)
            # If the file doesn't exist in the default Desktop but DOES exist in OneDrive Desktop
            if not os.path.exists(filepath) and os.path.exists(onedrive_filepath):
                filepath = onedrive_filepath
            # If neither exists but OneDrive Desktop is the primary (exists), default to it for new files
            elif not os.path.exists(filepath) and not os.path.exists(onedrive_desktop) is False:
                filepath = onedrive_filepath
                
        return filepath

    def create_file(self, filepath: str) -> str:
        filepath = self._normalize_path(filepath)
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, 'w') as f:
            pass
        return f"Created empty file '{filepath}'"

    def search_file(self, filename: str, directory: str = ".") -> str:
        directory = self._normalize_path(directory)
        found = []
        for root, _, files in os.walk(directory):
            for file in files:
                if filename.lower() in file.lower():
                    found.append(os.path.join(root, file))
        if not found:
            return f"No files found matching '{filename}'."
        return f"Found {len(found)} files: " + ", ".join(found)

    def move_file(self, src: str, dest: str) -> str:
        src = self._normalize_path(src)
        dest = self._normalize_path(dest)
        if not os.path.exists(src):
            raise FileNotFoundError(f"Source file '{src}' not found.")
        shutil.move(src, dest)
        return f"Moved '{src}' to '{dest}'"
        
    def delete_file(self, filepath: str) -> str:
        filepath = self._normalize_path(filepath)
        os.remove(filepath)
        return f"Deleted '{filepath}'"

    def read_file(self, filepath: str, max_chars: int = 5000) -> str:
        filepath = self._normalize_path(filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filepath}' not found.")
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(max_chars)
        truncated_msg = " [Truncated]" if len(content) >= max_chars else ""
        return f"Content of '{filepath}':\n{content}{truncated_msg}"

    def write_file(self, filepath: str, content: str) -> str:
        filepath = self._normalize_path(filepath)
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{filepath}'"

    def append_file(self, filepath: str, content: str) -> str:
        filepath = self._normalize_path(filepath)
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully appended content to '{filepath}'"

    def copy_file(self, src: str, dest: str) -> str:
        src = self._normalize_path(src)
        dest = self._normalize_path(dest)
        if not os.path.exists(src):
            raise FileNotFoundError(f"Source file '{src}' not found.")
        dest_dir = os.path.dirname(dest)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src, dest)
        return f"Copied '{src}' to '{dest}'"

    def create_folder(self, folderpath: str) -> str:
        folderpath = self._normalize_path(folderpath)
        os.makedirs(folderpath, exist_ok=True)
        return f"Created folder '{folderpath}'"

    def list_directory(self, directory: str = ".") -> str:
        directory = self._normalize_path(directory)
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory '{directory}' does not exist.")
        entries = []
        for entry in os.scandir(directory):
            prefix = "[DIR]" if entry.is_dir() else "[FILE]"
            entries.append(f"{prefix} {entry.name}")
        if not entries:
            return f"Directory '{directory}' is empty."
        return f"Directory contents of '{directory}':\n" + "\n".join(entries[:50])
