from agents.file_agent import FileAgent
from agents.system_agent import SystemAgent
from agents.memory_agent import MemoryAgent
from agents.browser_agent import BrowserAgent

# Initialize agents
agents_registry = {
    "FileAgent": FileAgent(),
    "SystemAgent": SystemAgent(),
    "MemoryAgent": MemoryAgent(),
    "BrowserAgent": BrowserAgent()
}

def get_agent(agent_name: str):
    return agents_registry.get(agent_name)
