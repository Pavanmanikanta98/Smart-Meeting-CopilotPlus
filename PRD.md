# PRD: Smart Meeting Copilot+ (Multi-Agent AI Assistant)

## 1. Introduction / Overview

**Smart Meeting Copilot+** is a multi-agent AI system designed to automate post-meeting workflows. It receives a meeting audio (or transcript), processes it through specialized agents (summarization, insight extraction, action detection), and produces structured follow-up materials including bullet-point summaries, decision highlights, action items with owners, and email drafts.

The system is built as a showcase of LLM agent orchestration, NLP reasoning, and full-stack pipeline development for job-seeking purposes.

---

## 2. Goals

- Automatically convert audio recordings from business meetings into structured, actionable data.
- Demonstrate a modular, agent-based architecture using LangGraph or similar frameworks.
- Generate high-quality, readable summaries, insights, and task lists.
- Provide developer-friendly outputs (JSON) and end-user-friendly outputs (emails).
- Serve as a job-seeking project with strong technical depth.

---

## 3. User Stories

- As a **team lead**, I want to receive structured meeting summaries so that I can follow up with my team easily.
- As a **founder or sales head**, I want detailed summaries that capture every critical point from B2B/B2C meetings without missing small details.
- As a **recruiter or technical manager**, I want to assess the candidate’s ability to build complex multi-agent systems by reviewing this working demo.

---

## 4. Functional Requirements

1. The system must allow users to upload or stream meeting audio (MP3, WAV).
2. The system must transcribe the audio using Whisper or equivalent ASR models.
3. The system must route the transcription through a **Summarization Agent** to generate key summaries and decisions.
4. The system must route the same transcription through an **Action Extraction Agent** to identify tasks, owners, and deadlines.
5. The system must use a **Controller Agent** to coordinate routing and merge outputs.
6. The system must optionally include a **Follow-Up Email Agent** that composes emails from the structured data.
7. The system must output:
   - JSON format (summary, insights, actions)
   - Plain text or HTML email drafts
8. The architecture must be modular and agent-based, built using LangGraph or LangChain.
9. Future phase: Expose core workflow via FastAPI.
10. Future phase: Build frontend using React/Next.js to demo the pipeline.

---

## 5. Non-Goals (Out of Scope)

- Real-time UI or browser-based streaming meetings
- Integration with Zoom/Google Meet APIs
- Human-in-the-loop corrections or feedback features

---

## 6. Design Considerations (Optional)

- UI and UX are not required in this phase; the focus is backend logic.
- CLI-based testing or notebook demos are acceptable.
- JSON outputs should be clearly structured for easy frontend integration later.

---

## 7. Technical Considerations (Optional)

- Must be runnable locally (offline transcript + LLM calls)
- Use only free-tier or open-source APIs:
  - Whisper (OpenAI or faster Whisper.cpp)
  - LLMs: GPT-3.5/GPT-4 via Groq, Gemini Pro, Hugging Face models like Mixtral
- LangGraph (preferred) or LangChain for agent management
- Should support clean error handling and extensibility

---

## 8. Success Metrics

- Summary is concise and contextually accurate
- Insights capture decisions and key takeaways
- At least 80% of action items are clearly extracted
- Follow-up email is readable, polite, and accurate
- System is modular, testable, and runs locally with sample inputs

---

## 9. Open Questions

- Will frontend users authenticate (or is this purely demo-based)?
- Should each agent's output be logged separately for debugging?
- Should follow-up email be split per user or one combined thread?
- Should email format support language localization (EN only or more)?

