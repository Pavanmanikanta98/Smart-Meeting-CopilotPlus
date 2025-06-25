# Developer Task List – Smart Meeting Copilot+

This task list breaks down the work based on the Product Requirements Document (PRD). The project is split into two major implementations: **Agent Workflow Prototyping (Notebook)** and **Backend API Integration**, plus a basic **Frontend interface**.

---

## ✅ 1. Backend – A: Notebook-based Agent Workflow (MVP Prototype)

_These tasks aim to get a fully working LangGraph/LangChain multi-agent workflow inside a Jupyter notebook before API wrapping._

### 🔁 Setup
- [ ] Set up Python virtual environment
- [ ] Install required packages (`langgraph`, `openai`, `whisper`, `transformers`, `pydantic`, etc.)
- [ ] Create sample audio files and transcripts in `data/`

### 🧠 Core Agents
- [ ] Implement `Summarization Agent` to extract bullet-point summaries
- [ ] Implement `Insights Agent` to highlight decisions, blockers, key moments
- [ ] Implement `Action Item Agent` to extract:
  - Task
  - Owner (person)
  - Deadline (if any)
  - Priority (optional)
- [ ] Implement `Email Generator Agent` (summary + actions → professional email)
- [ ] Design and implement `Super Agent` (routes inputs to correct agents and merges output)

### 🧪 Evaluation & Debugging
- [ ] Create test notebook with transcript samples
- [ ] Log outputs of each agent step-by-step
- [ ] Store intermediate results as structured JSON

---

## ✅ 2. Backend – B: FastAPI-Based Modular API

_After the core logic is validated in notebooks, wrap it as reusable backend APIs._

### 📁 Structure Setup
- [ ] Create `smartcopilot-api/` FastAPI project with:
  - `src/`
  - `tools/`
  - `routes/`
  - `models/`
- [ ] Add project scaffolding: `pyproject.toml`, `Dockerfile`, `Makefile`

### 🚏 API Endpoints
- [ ] `POST /transcribe`: Accept audio file and return transcript
- [ ] `POST /analyze`: Accept transcript and run all agents
- [ ] `POST /summary`: Return summary and key insights
- [ ] `POST /actions`: Return structured list of action items
- [ ] `POST /email`: Return email draft (summary and/or actions)

### 🧪 Testing
- [ ] Add test scripts for each endpoint (e.g., with `httpx` or `pytest`)
- [ ] Validate error handling, timeouts, and invalid input flows

---

## ✅ 3. Frontend (React / Next.js)

_Simple UI for uploading a file and displaying results._

### 🏗️ Setup
- [ ] Initialize project using `npx create-react-app` or `create-next-app`
- [ ] Install Axios or fetch wrapper for API calls

### 🔌 Features
- [ ] Page: Upload Audio File
- [ ] Show: Transcription output
- [ ] Show: Bullet-point meeting summary
- [ ] Show: Extracted action items (table format)
- [ ] Show: Suggested email draft (editable textarea)

### 💡 UX Considerations
- [ ] Loading states
- [ ] Minimal error messages and retry option
- [ ] Option to copy email to clipboard

---

## 🔄 Optional Future Enhancements

- [ ] Integrate with Gmail API to send email directly
- [ ] Add multi-user authentication and saved transcripts
- [ ] Add real-time audio streaming transcription
- [ ] Enable team-specific models or prompt tuning
