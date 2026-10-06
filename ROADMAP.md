# AI Operating System (AI OS) — System Audit & Action Roadmap

This document outlines the current state of the AI OS project, identified technical debt and bugs, pending phases, and an actionable roadmap for upcoming features based on [`AI_OS_Architecture(1).md`](file:///d:/brawlhalla/Project%201/AI_OS_Architecture(1).md) and [`implementation_plan.md`](file:///d:/brawlhalla/Project%201/implementation_plan.md).

---

## 1. Executive Summary & Current Status

The AI OS enables natural language interaction with Windows through a multi-agent hierarchy orchestrated by Google Gemini.

### Completed Components
- **Backend Framework**: FastAPI server running with CORS support ([`backend/main.py`](file:///d:/brawlhalla/Project%201/backend/main.py)).
- **LLM Reasoning Core**: Gemini client with `tenacity` exponential backoff retry logic to handle free tier rate limits ([`backend/ai_core.py`](file:///d:/brawlhalla/Project%201/backend/ai_core.py)).
- **Planner Agent**: Natural-language instruction decomposition into structured JSON action plans ([`backend/planner_agent.py`](file:///d:/brawlhalla/Project%201/backend/planner_agent.py)).
- **Multi-Agent Routing & Registry**: Dynamic agent registry ([`backend/agents/registry.py`](file:///d:/brawlhalla/Project%201/backend/agents/registry.py)) and step execution loop ([`backend/executor.py`](file:///d:/brawlhalla/Project%201/backend/executor.py)).
- **File Agent**: Path normalization (handling Windows OneDrive desktop folder redirection), file creation, search, moving, and deletion ([`backend/agents/file_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/file_agent.py)).
- **System Agent**: Application launching via PowerShell and Desktop `.lnk` shortcut scanning, process termination via `taskkill`, raw shell execution ([`backend/agents/system_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/system_agent.py)).
- **Safety Layer**: Interception of high-risk tools (`delete_file`, `system_command`) and human verification approval loop via UI ([`backend/tools/base.py`](file:///d:/brawlhalla/Project%201/backend/tools/base.py), [`frontend/src/app/page.tsx`](file:///d:/brawlhalla/Project%201/frontend/src/app/page.tsx)).

---

## 2. Critical Fixes & Technical Debt (Priority 1)

These issues exist in current code and should be resolved before adding new capabilities.

### 2.1 Multi-Step Plan Resumption Bug After Human Approval
- **File**: [`backend/main.py`](file:///d:/brawlhalla/Project%201/backend/main.py#L29-L43), [`backend/executor.py`](file:///d:/brawlhalla/Project%201/backend/executor.py#L36-L45)
- **Problem**: When a multi-step plan encounters a high-risk tool (e.g., Step 2 requires confirmation), execution halts and returns a `pending_action` to the frontend. When the user approves Step 2, `main.py` only executes that single step and immediately concludes. Any subsequent steps (Steps 3, 4, etc.) are permanently dropped.
- **Solution**: 
  - Save the remaining plan or pass a `plan_id` / full remaining step list in the approval payload.
  - Resume the executor loop from `step_number + 1` until all steps complete or another safety check triggers.

### 2.2 Stateless Context & Conversation Memory Loss
- **File**: [`backend/planner_agent.py`](file:///d:/brawlhalla/Project%201/backend/planner_agent.py#L4-L45), [`backend/main.py`](file:///d:/brawlhalla/Project%201/backend/main.py#L21-L24)
- **Problem**: Every request creates a brand new plan with zero conversation history. If the user asks *"Find my resume"*, and then *"Move it to Documents"*, the LLM does not know what resume file was previously found or what happened in prior turns.
- **Solution**:
  - Accept conversation history in `ChatRequest`.
  - Supply recent messages and tool outputs (e.g., intermediate findings) to the Gemini prompt context in `create_plan`.

### 2.3 Orphaned & Missing Tools
- **Files**: [`backend/tools_impl.py`](file:///d:/brawlhalla/Project%201/backend/tools_impl.py), [`backend/agents/file_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/file_agent.py), [`backend/agents/system_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/system_agent.py)
- **Problem**: Functions `read_file`, `write_file`, and `list_directory` in `tools_impl.py` are unused and not registered to any agent or exposed to the Planner Agent.
- **Solution**:
  - Move file manipulation tools (`read_file`, `write_file`, `append_file`, `create_folder`, `copy_file`) into `FileAgent` with OneDrive path normalization.
  - Add system inspection tools to `SystemAgent` (`get_system_info` for CPU/RAM/Disk stats, `list_processes` for running tasks).
  - Update tool definitions in `planner_agent.py` so the LLM knows how to call them.

### 2.4 Missing `requirements.txt`
- **File**: [`backend/requirements.txt`](file:///d:/brawlhalla/Project%201/backend/)
- **Problem**: The backend virtual environment exists locally, but there is no dependency manifest.
- **Solution**: Generate a clean `requirements.txt` listing `fastapi`, `uvicorn`, `google-generativeai`, `tenacity`, `pydantic`, `python-dotenv`, and `psutil`.

---

## 3. Phase 4: Memory Architecture (Priority 2)

Implementing context persistence across interactions.

### 3.1 Short-Term Memory
- **Module**: `backend/memory/short_term.py`
- In-memory rolling window of recent queries, planner steps, and tool execution outputs.
- Retains variable bindings across multi-step conversations (e.g., `$FOUND_FILE = "C:/Users/.../resume.pdf"`).

### 3.2 Long-Term Structured Memory (SQLite)
- **Module**: `backend/memory/db.py`
- **Tables**:
  - `preferences`: Key-value storage for user defaults (e.g. `default_browser`, `download_path`, `preferred_text_editor`, `username`).
  - `task_history`: Logs of previous queries, plans generated, execution results, and timestamps.
- **Capabilities**:
  - Allows the AI to remember: *"User prefers Chrome"*, *"User likes saving reports in D:/Projects"*.

### 3.3 Semantic Memory (Vector Search)
- **Module**: `backend/memory/semantic.py`
- Integration with ChromaDB or SQLite FTS with embeddings.
- Stores common workflows and past solutions so repeated instructions (e.g. *"Prepare my coding setup"*) can retrieve proven plans immediately.

---

## 4. Phase 3 Extensions: Additional Specialized Agents (Priority 3)

### 4.1 Browser Agent
- **Module**: `backend/agents/browser_agent.py`
- **Library**: Playwright (`playwright-python`)
- **Tools**:
  - `search_web(query)`: Search Google/Bing and return top answers.
  - `open_url(url)`: Open a web page in headless or standard mode.
  - `extract_page_content(url)`: Scrape text and summarize articles.

### 4.2 Document Agent
- **Module**: `backend/agents/document_agent.py`
- **Libraries**: `pypdf`, `python-docx`
- **Tools**:
  - `read_pdf(filepath)`: Extract text from PDF documents.
  - `read_docx(filepath)`: Extract text from Word documents.
  - `summarize_document(filepath)`: Read and summarize content using Gemini.

### 4.3 Email & Calendar Agents
- **Module**: `backend/agents/email_agent.py`, `backend/agents/calendar_agent.py`
- **Integration**: Google Workspace APIs (Gmail, Google Calendar) or Windows protocol handlers.
- **Safety**: Email sending and event deletion are flagged as `high_risk=True` to require user confirmation.

---

## 5. Phase 5 & 6: Voice, Vision & Desktop UI (Priority 4)

Upgrading the frontend from a minimal chat box into an authentic AI OS dashboard.

### 5.1 Voice Interaction (Phase 5)
- **Speech-to-Text**: Web Speech API (`webkitSpeechRecognition`) for browser microphone input, or backend endpoint using `faster-whisper`.
- **Text-to-Speech**: Browser `window.speechSynthesis` or backend `edge-tts` for natural vocal feedback.
- **UI**: Interactive microphone toggle with active listening waves.

### 5.2 Desktop OS User Interface (Phase 6)
- **Location**: [`frontend/src/app/page.tsx`](file:///d:/brawlhalla/Project%201/frontend/src/app/page.tsx)
- **Key UI Components**:
  - **Live Step Progress Stepper**: Visual timeline showing steps with statuses: `Pending` (grey), `Executing` (pulsing blue), `Awaiting Approval` (amber), `Completed` (emerald), `Failed` (rose).
  - **Agent Activity Dashboard**: Real-time cards showing active agents (FileAgent, SystemAgent, BrowserAgent).
  - **System Overview Widget**: Live CPU, RAM, and Disk space gauges (powered by SystemAgent).
  - **Quick Action Chips**: One-click actions (*"System Health"*, *"Clean Temp Files"*, *"Organize Downloads"*, *"Open Dev Workspace"*).
  - **Live Streaming**: Transition from single POST request to Server-Sent Events (SSE) or WebSockets for real-time progress streaming.

---

## 6. Phase 7: GUI Automation & Vision (Priority 5)

For legacy desktop software and applications lacking APIs:
- **PyAutoGUI Automation**: Simulate mouse clicks, coordinate navigation, and keystrokes.
- **Vision Model Integration**: Capture Windows screenshots via `Pillow` / `mss` and submit to Gemini Vision to detect button coordinates and UI state.

---

## 7. Action Plan Checklist

| Status | Phase | Task Description | Target Files |
| :---: | :---: | :--- | :--- |
| [x] | **Fix** | Fix multi-step execution resumption after human approval | [`backend/main.py`](file:///d:/brawlhalla/Project%201/backend/main.py), [`backend/executor.py`](file:///d:/brawlhalla/Project%201/backend/executor.py) |
| [x] | **Fix** | Move orphaned tools (`read_file`, `write_file`, `list_dir`, `copy_file`) to `FileAgent` and update `planner_agent.py` | [`backend/agents/file_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/file_agent.py), [`backend/planner_agent.py`](file:///d:/brawlhalla/Project%201/backend/planner_agent.py) |
| [x] | **Fix** | Add system monitoring tools (`get_system_info`, `list_processes`) | [`backend/agents/system_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/system_agent.py) |
| [x] | **Fix** | Generate `requirements.txt` for backend | [`backend/requirements.txt`](file:///d:/brawlhalla/Project%201/backend/requirements.txt) |
| [x] | **Phase 4** | Implement conversation session history in `ChatRequest` & `create_plan` | [`backend/main.py`](file:///d:/brawlhalla/Project%201/backend/main.py), [`backend/planner_agent.py`](file:///d:/brawlhalla/Project%201/backend/planner_agent.py) |
| [x] | **Phase 4** | Implement SQLite long-term memory for preferences and past plans | [`backend/memory/db.py`](file:///d:/brawlhalla/Project%201/backend/memory/db.py), [`backend/agents/memory_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/memory_agent.py) |
| [x] | **Phase 3** | Implement Browser Agent with Playwright / Web Search | [`backend/agents/browser_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/browser_agent.py) |
| [ ] | **Phase 3** | Implement Document Agent for PDF and text processing | `backend/agents/document_agent.py` |
| [ ] | **Phase 5** | Add microphone input (Voice-to-Text) and audio response (TTS) | [`frontend/src/app/page.tsx`](file:///d:/brawlhalla/Project%201/frontend/src/app/page.tsx) |
| [ ] | **Phase 6** | Build live step execution stepper and agent status indicators in UI | [`frontend/src/app/page.tsx`](file:///d:/brawlhalla/Project%201/frontend/src/app/page.tsx) |
