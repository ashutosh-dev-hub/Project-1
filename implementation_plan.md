# AI Operating System (AI OS) Implementation Plan

This document outlines the technical implementation plan for the AI OS project, based on the `AI_OS_Architecture(1).md` specification. The AI OS translates natural-language instructions into system actions via an LLM, a Planner Agent, and a Multi-Agent system executing on the underlying OS.

## Proposed Changes

We will follow the 7-phase development approach suggested in the architecture document.

---

### Phase 1: Basic AI OS (Foundation) - **[COMPLETED]**

This phase establishes the core communication between the frontend, backend, and the LLM, enabling basic text commands and simple system/file operations.

#### [NEW] Backend Setup (`d:\brawlhalla\Project 1\backend\`)
- [x] Initialize a Python FastAPI project.
- [x] Set up the Gemini API client. *Note: We will use the free Gemini API key. We will implement robust retry logic with exponential backoff to handle the 15 Requests-Per-Minute (RPM) limit of the free tier.*
- [x] Create endpoints for receiving text input and returning responses.

#### [NEW] Frontend Setup (`d:\brawlhalla\Project 1\frontend\`)
- [x] Initialize a React/Next.js project.
- [x] Create a basic chat-like interface for text input.
- [x] Connect to the FastAPI backend.
- [x] Display task execution progress and results.

---

### Phase 2: Intelligent Planning - **[IN PROGRESS]**

Introduce the Planner Agent to decompose complex tasks into multi-step execution plans.

#### [NEW] Planner Module (`backend/planner_agent.py`, `backend/executor.py`)
- [x] Create the Planner Agent responsible for breaking down high-level requests into sequential steps.
- [x] Implement a structured JSON response format for the LLM to output task plans (and conversational chat).
- [x] Implement an Executor module that processes the plan step-by-step.
- [ ] Fix multi-step plan execution resumption after user human approval.
- [ ] Add error handling and replanning logic if a step fails.

---

### Phase 3: Multi-Agent System - **[IN PROGRESS]**

Distribute responsibilities to specialized agents.

#### [NEW] Agent Modules (`backend/agents/`)
- [x] **File Agent**: Implement search, move, delete, create (with OneDrive Desktop sync normalization).
- [x] **File Agent Extensions**: Implement file reading, writing, copying, folder creation, and directory listing.
- [x] **System Agent**: Implement open/close applications (with `.lnk` shortcut scanning for games like Valorant) and raw command execution.
- [x] **System Agent Extensions**: Implement system info tools (CPU, RAM, Disk) and process monitoring.
- [x] **Browser Agent**: Integrate web search, URL launching, and page extraction ([`backend/agents/browser_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/browser_agent.py)).
- [ ] **Email Agent**: Integrate Gmail API for drafting/sending emails.
- [ ] **Calendar Agent**: Integrate Google Calendar API for event management.
- [ ] **Document Agent**: Implement basic text extraction and summarization.

#### [NEW] Tool Layer (`backend/tools/`)
- [x] Define strict tool interfaces.
- [x] Add the **Validation and Safety Layer** to intercept high-risk operations.
- [x] Enforce human verification/approval before execution natively in the UI with an "Approve Execution" button.

---

### Phase 4: Memory Architecture - **[IN PROGRESS]**

Implement short-term and long-term memory to retain context.

#### [NEW] Memory Module (`backend/memory/`)
- [x] **Short-Term Memory**: Multi-turn conversation history and task state passed to Planner.
- [x] **Long-Term Memory**: SQLite database for user preferences, memory facts, and workflow history ([`backend/memory/db.py`](file:///d:/brawlhalla/Project%201/backend/memory/db.py), [`backend/agents/memory_agent.py`](file:///d:/brawlhalla/Project%201/backend/agents/memory_agent.py)).
- [ ] **Semantic Memory**: Integrate FAISS or ChromaDB with an embedding model to store and retrieve previous workflows.

---

### Phase 5: Voice and Vision (GUI) Integration

Enable voice interactions and computer vision for GUI automation.

#### [NEW] GUI & Vision Agent
- [ ] **GUI Control**: Integrate PyAutoGUI to click buttons and navigate interfaces based on visual context (e.g., clicking "Play" in Riot Client).
- [ ] **Vision Capabilities**: Capture screenshots and send them to Gemini Vision to "see" what is on the screen and determine bounding boxes for clicks.

#### [MODIFY] Frontend UI (`d:\brawlhalla\Project 1\frontend\`)
- [ ] Add microphone recording capabilities and voice visualization.
- [ ] Implement audio playback for TTS.

---

### Phase 6 & 7: GUI Polish and Final Integration

Finalize the user experience and ensure end-to-end reliability.

#### [MODIFY] Frontend Polish (`frontend/`)
- Enhance the Next.js UI to be a desktop-class web interface.
- Implement WebSocket connections for real-time task status updates and agent activity streams.
- Add rich confirmation dialogs for the safety validation layer.

#### [MODIFY] End-to-End Testing & Integration
- Test the full pipeline: Text/Voice -> LLM -> Planner -> Multi-Agent -> Tools -> Safety Validator -> OS Execution -> Memory -> Response.
- Perform end-to-end testing with complex workflow scenarios (e.g., "Prepare my interview workspace").

## Verification Plan

### Automated Tests
- `pytest` for backend unit testing (Planner logic, Tool execution, Agent routing).
- `jest` or `vitest` for frontend component testing.
- Playwright tests for validating the Browser Agent functionality.

### Manual Verification
- Manually run the application on Windows.
- Issue complex commands (e.g., "Find my resume, rename it to Ashutosh_Resume.pdf and move it to Documents") and verify:
  1. The Planner breaks down the task correctly.
  2. The File Agent locates and moves the file.
  3. The Safety Layer prompts for confirmation if required.
  4. The Memory records the action.
  5. The UI updates in real-time.
