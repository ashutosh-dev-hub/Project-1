from tools.base import Tool, ToolResponse
from typing import Dict, Any

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def execute_tool(self, tool_name: str, bypass_safety: bool = False, **kwargs) -> ToolResponse:
        if tool_name not in self.tools:
            return ToolResponse(result="", error=f"Tool '{tool_name}' not found in {self.name}.")
        return self.tools[tool_name].execute(bypass_safety=bypass_safety, **kwargs)
