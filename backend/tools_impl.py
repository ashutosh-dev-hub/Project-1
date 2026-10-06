import os
import subprocess
from typing import Optional
from pydantic import BaseModel

class ToolResponse(BaseModel):
    result: str
    error: Optional[str] = None

def execute_system_command(command: str) -> ToolResponse:
    """Execute a simple system command."""
    try:
        # Note: In a real system, strict validation of `command` is required.
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return ToolResponse(result=result.stdout)
        else:
            return ToolResponse(result="", error=result.stderr)
    except Exception as e:
        return ToolResponse(result="", error=str(e))

def list_directory(path: str) -> ToolResponse:
    """List contents of a directory."""
    try:
        files = os.listdir(path)
        return ToolResponse(result="\n".join(files))
    except Exception as e:
        return ToolResponse(result="", error=str(e))

def read_file(path: str) -> ToolResponse:
    """Read the contents of a file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return ToolResponse(result=f.read())
    except Exception as e:
        return ToolResponse(result="", error=str(e))

def write_file(path: str, content: str) -> ToolResponse:
    """Write contents to a file."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return ToolResponse(result="Success")
    except Exception as e:
        return ToolResponse(result="", error=str(e))
