# AI Operating System (AI OS)

An intelligent natural-language operating system layer running on Windows. Translates high-level natural language instructions into multi-agent system execution plans orchestrated by Google Gemini.

---

## 🚀 Overview

Instead of manually clicking through multiple applications, files, and browsers, the AI OS decomposes commands into structured execution graphs executed by specialized agents with a built-in safety validation layer.

```text
User Command: "Find my resume, save note that it's updated, and search the web for FastAPI jobs."
       │
       ▼
   LLM AI Core (Google Gemini Reasoning)
       │
       ▼
   Planner Agent (Task Decomposition & JSON Schema)
       │
       ├─────────────────┬──────────────────┬─────────────────┐
       ▼                 ▼                  ▼                 ▼
   File Agent       System Agent       Memory Agent      Browser Agent
 (Files & Folders) (Apps & Diag)     (SQLite Context)    (Web Search)
       │                 │                  │                 │
       └─────────────────┴──────────────────┴─────────────────┘
                                 │
                                 ▼
                     Safety & Validation Layer
                 (Intercepts High-Risk Actions)
                                 │
                                 ▼
                      Windows OS Execution
```

---

## 📊 Current Progress & Status

| Phase | Component | Status | Description |
| :---: | :--- | :---: | :--- |
| **1** | **Backend & Frontend Foundation** | ✅ **Completed** | FastAPI backend with Gemini API exponential retry backoff + Next.js chat interface. |
| **2** | **Intelligent Planning & Replanning** | ✅ **Completed** | Structured JSON plan generation, step executor, and automated LLM replanning on tool failures. |
| **3** | **Multi-Agent System** | 🔄 **In Progress** | FileAgent, SystemAgent, MemoryAgent, BrowserAgent complete. Document & Email agents upcoming. |
| **4** | **Memory Architecture** | 🔄 **In Progress** | Short-term conversation history + Long-Term SQLite database for user preferences & task history complete. |
| **5** | **Voice & Vision Integration** | ⏳ **Upcoming** | Speech-to-Text, Audio TTS playback, and PyAutoGUI screen control. |
| **6** | **Desktop OS UI & Live Stepper** | ⏳ **Upcoming** | Live step status timeline, agent activity gauges, and WebSocket streaming. |

---

## 🛠️ Specialized Agents & Tools

### 1. FileAgent ([`backend/agents/file_agent.py`](backend/agents/file_agent.py))
- `search_file`: Search files across directory trees.
- `read_file` & `write_file` / `append_file`: Read and write file contents with automatic folder creation.
- `copy_file` & `move_file`: Move, rename, or copy files.
- `create_file` & `create_folder`: Create empty files and directories.
- `delete_file`: Safe deletion with mandatory **Human Verification** interception.
- *OneDrive Sync Normalization*: Automatically resolves Windows 11 OneDrive desktop folder redirections.

### 2. SystemAgent ([`backend/agents/system_agent.py`](backend/agents/system_agent.py))
- `open_application`: Launches desktop applications via PowerShell and scans `.lnk` shortcuts (Valorant, Steam, etc.).
- `close_application`: Terminates running applications via `taskkill`.
- `get_system_info`: Reports live CPU utilization, logical core count, RAM usage, and Disk C: capacity.
- `list_processes`: Lists running processes sorted by memory utilization.
- `system_command`: Executes raw shell commands (**High-Risk**; requires approval).

### 3. MemoryAgent ([`backend/agents/memory_agent.py`](backend/agents/memory_agent.py))
- `set_user_preference` / `get_user_preferences`: Persistent user configuration stored in SQLite (`backend/memory/ai_os_memory.db`).
- `save_memory_fact` / `search_memory_facts`: Stores arbitrary user notes and learned facts.
- `get_execution_history`: Retrieves previous execution tasks and status logs.
- *Context Injection*: Stored preferences are automatically injected into the Planner prompt so the AI remembers choices (e.g. preferred browser).

### 4. BrowserAgent ([`backend/agents/browser_agent.py`](backend/agents/browser_agent.py))
- `search_web`: Live internet queries via DuckDuckGo returning structured titles, snippets, and source URLs.
- `open_url`: Launches websites on your desktop in your preferred browser (Brave, Chrome, Edge).
- `extract_page_content`: Scrapes and extracts readable article text from URLs using BeautifulSoup.

---

## 🗺️ Detailed Documentation & Plan

- [**`ROADMAP.md`**](ROADMAP.md) — Technical debt audit, bug tracking, and step-by-step feature roadmap.
- [**`implementation_plan.md`**](implementation_plan.md) — Official 7-phase implementation checklist.
- [**`AI_OS_Architecture(1).md`**](AI_OS_Architecture(1).md) — Complete high-level system architecture specification.
- [**`memory.md`**](memory.md) — Architectural decision log and memory notes.

---

## ⚙️ Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API Key (Free Tier)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # On Windows

pip install -r requirements.txt

# Create .env from template
copy .env.example .env
# Edit .env and paste your GEMINI_API_KEY

# Start backend server
uvicorn main:app --reload --port 8000
```
Backend runs on `http://127.0.0.1:8000`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🛡️ Safety & Validation Layer

The AI OS enforces a human-in-the-loop safety model:
1. When an agent attempts a high-risk operation (`delete_file`, `system_command`), execution is immediately paused.
2. A verification card appears in the chat UI detailing the exact tool and parameters.
3. Once the user clicks **"Approve & Resume Execution"**, the backend executes the approved action and continues subsequent planned steps.
