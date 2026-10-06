from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel

class ToolResponse(BaseModel):
    result: str
    error: Optional[str] = None
    needs_confirmation: bool = False

class Tool:
    def __init__(self, name: str, description: str, func: Callable, high_risk: bool = False):
        self.name = name
        self.description = description
        self.func = func
        self.high_risk = high_risk

    def execute(self, bypass_safety: bool = False, **kwargs) -> ToolResponse:
        """
        Execute the tool function. Integrates the Safety Validator Layer.
        """
        if self.high_risk and not bypass_safety:
            # For Phase 3, we simulate intercepting for human approval.
            return ToolResponse(
                result=f"Blocked: Execution of high-risk tool '{self.name}' requires human verification.",
                needs_confirmation=True
            )
        try:
            result = self.func(**kwargs)
            return ToolResponse(result=str(result))
        except Exception as e:
            return ToolResponse(result="", error=str(e))
