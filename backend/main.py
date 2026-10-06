from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from planner_agent import create_plan
from executor import execute_plan
from agents.registry import get_agent
from memory.db import (
    log_task,
    get_all_preferences,
    set_preference,
    delete_preference,
    get_memory_facts,
    add_memory_fact,
    get_recent_tasks
)

app = FastAPI(title="AI OS Backend", version="1.0.0")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None
    pending_action_approved: Optional[Dict[str, Any]] = None

class PreferenceRequest(BaseModel):
    key: str
    value: str
    description: Optional[str] = ""

class FactRequest(BaseModel):
    topic: str
    content: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    logs = []
    try:
        # Route 1: Resuming an approved action (with multi-step plan continuity)
        if request.pending_action_approved:
            action = request.pending_action_approved
            plan = action.get("plan")
            step_index = action.get("step_index", 0)
            user_query = action.get("user_query", "")
            
            if plan and "steps" in plan:
                logs, pending_action = execute_plan(
                    plan=plan,
                    user_query=user_query,
                    start_step_index=step_index,
                    bypass_first_safety=True
                )
                status = "awaiting_approval" if pending_action else "completed"
                log_task(user_query=f"[Approved Step {action.get('step_number')}] {user_query}", plan=plan, status=status, logs=logs)
                
                status_suffix = " (Subsequent action requires confirmation)." if pending_action else " Successfully finished all steps."
                reply = f"Resumed execution from Step {action.get('step_number', step_index + 1)}.{status_suffix}"
                return {
                    "reply": reply,
                    "agent_logs": logs,
                    "pending_action": pending_action
                }
            else:
                # Standalone action execution fallback
                logs = [f"Resuming execution: User approved Step {action.get('step_number')}"]
                agent = get_agent(action["agent_name"])
                if not agent:
                    logs.append(f"-> Error: Agent {action['agent_name']} not found.")
                    return {"reply": "Execution failed.", "agent_logs": logs, "pending_action": None}
                    
                response = agent.execute_tool(action["tool_name"], bypass_safety=True, **action.get("arguments", {}))
                if response.error:
                    logs.append(f"-> Error executing tool: {response.error}")
                else:
                    logs.append(f"-> Success: {response.result}")
                logs.append("Plan execution completed.")
                log_task(user_query=f"[Approved Standalone] {action['tool_name']}", status="completed", logs=logs)
                return {"reply": "Execution resumed and completed.", "agent_logs": logs, "pending_action": None}

        # Route 2: Standard user message request
        plan = create_plan(request.message, history=request.history)
        logs, pending_action = execute_plan(plan, user_query=request.message)
        
        status = "awaiting_approval" if pending_action else "completed"
        log_task(user_query=request.message, plan=plan, status=status, logs=logs)
        
        reply = plan.get("response", "I have processed your request.")
        if plan and plan.get("steps"):
            steps_text = "\n".join([f"- Step {s.get('step_number', idx+1)}: {s.get('description', '')} (Agent: {s.get('target_agent')})" for idx, s in enumerate(plan.get("steps", []))])
            reply += f"\n\nPlanned Steps:\n{steps_text}"

        return {
            "reply": reply,
            "agent_logs": logs,
            "pending_action": pending_action
        }
    except Exception as e:
        logs.append(f"Fatal error encountered: {str(e)}")
        log_task(user_query=request.message or "Unknown", status="failed", logs=logs)
        raise HTTPException(status_code=500, detail={"error": str(e), "logs": logs})

# --- Memory Endpoints ---

@app.get("/api/memory/preferences")
async def get_preferences_endpoint():
    """Returns all stored user preferences."""
    return {"preferences": get_all_preferences()}

@app.post("/api/memory/preferences")
async def set_preference_endpoint(req: PreferenceRequest):
    """Sets or updates a user preference."""
    res = set_preference(req.key, req.value, req.description or "")
    return {"status": "ok", "preference": res}

@app.delete("/api/memory/preferences/{key}")
async def delete_preference_endpoint(key: str):
    """Deletes a user preference."""
    success = delete_preference(key)
    return {"status": "ok" if success else "not_found"}

@app.get("/api/memory/facts")
async def get_facts_endpoint(topic: Optional[str] = None):
    """Retrieves long-term memory notes and facts."""
    return {"facts": get_memory_facts(topic)}

@app.post("/api/memory/facts")
async def add_fact_endpoint(req: FactRequest):
    """Stores a new memory note or fact."""
    fact_id = add_memory_fact(req.topic, req.content)
    return {"status": "ok", "id": fact_id}

@app.get("/api/memory/history")
async def get_history_endpoint(limit: int = 15):
    """Returns recent task execution history."""
    return {"history": get_recent_tasks(limit=limit)}

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}
