from agents.base import BaseAgent
from tools.base import Tool
from memory.db import (
    set_preference,
    get_preference,
    get_all_preferences,
    add_memory_fact,
    get_memory_facts,
    get_recent_tasks
)

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("MemoryAgent")
        self.register_tool(Tool(
            "set_user_preference", 
            "Store or update a persistent user preference (e.g. key='default_browser', value='brave')", 
            self.set_user_preference
        ))
        self.register_tool(Tool(
            "get_user_preferences", 
            "Retrieve all stored user preferences", 
            self.get_user_preferences
        ))
        self.register_tool(Tool(
            "save_memory_fact", 
            "Save a custom fact or note for long-term recall", 
            self.save_memory_fact
        ))
        self.register_tool(Tool(
            "search_memory_facts", 
            "Search stored notes and facts by topic keyword", 
            self.search_memory_facts
        ))
        self.register_tool(Tool(
            "get_execution_history", 
            "Get recent tasks executed by AI OS", 
            self.get_execution_history
        ))

    def set_user_preference(self, key: str, value: str, description: str = "", **kwargs) -> str:
        if not key or not value:
            raise ValueError("Both 'key' and 'value' are required.")
        set_preference(key, value, description)
        return f"Successfully saved preference: '{key}' = '{value}'"

    def get_user_preferences(self, **kwargs) -> str:
        prefs = get_all_preferences()
        if not prefs:
            return "No custom preferences stored."
        lines = [f"- {k}: {v}" for k, v in prefs.items()]
        return "Current Stored Preferences:\n" + "\n".join(lines)

    def save_memory_fact(self, topic: str, content: str, **kwargs) -> str:
        if not topic or not content:
            raise ValueError("Both 'topic' and 'content' are required.")
        fact_id = add_memory_fact(topic, content)
        return f"Saved memory note (ID: {fact_id}) under topic '{topic}'."

    def search_memory_facts(self, topic: str = "", **kwargs) -> str:
        facts = get_memory_facts(topic=topic if topic else None)
        if not facts:
            return f"No memory facts found for topic '{topic}'." if topic else "No stored memory facts."
        lines = [f"- [{f['topic']}] ({f['timestamp']}): {f['content']}" for f in facts]
        return f"Found {len(facts)} memory facts:\n" + "\n".join(lines)

    def get_execution_history(self, limit: int = 5, **kwargs) -> str:
        history = get_recent_tasks(limit=int(limit))
        if not history:
            return "No previous execution history found."
        lines = [f"- [{h['timestamp']}] ({h['status']}): {h['user_query']}" for h in history]
        return f"Recent Tasks ({len(history)} shown):\n" + "\n".join(lines)
