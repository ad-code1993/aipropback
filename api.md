# 📚 API Documentation: AI Proposal Generator Backend

---

## Overview
This document describes the available API endpoints for the AI Proposal Generator backend, their expected input/output, and a summary of their implementation.

---

## 1. POST `/start_proposal`
**Purpose:** Start a new interactive proposal session.

**Request Body:** _None_

**Response Example:**
```json
{
  "session_id": "b1c2d3e4-5678-90ab-cdef-1234567890ab",
  "question": "Reason: To understand who the proposal is for.\nQuestion: What is the client's name or organization?"
}
```

**Implementation:**
- Generates a unique `session_id`.
- Starts a conversation with the AI agent, returning the first question.
- Stores the session and conversation history in the database.

---

## 2. POST `/continue_proposal/{session_id}`
**Purpose:** Continue the proposal Q&A by submitting an answer and receiving the next question or the completed proposal.

**Request Body Example:**
```json
{
  "response": "We aim to automate hiring processes."
}
```

**Response Example (next question):**
```json
{
  "question": "Reason: To clarify the main goal.\nQuestion: What are the main goals of the project?"
}
```

**Response Example (completed):**
```json
{
  "completed": true,
  "proposal": {
    "client_name": "Acme Corp",
    "project_title": "AI Hiring Automation",
    "project_goals": "Automate candidate screening and scheduling.",
    "timeline": "Q3 2025",
    "deliverables": "Web app, documentation, deployment",
    "technologies": "Python, FastAPI, SQLModel, Gemini AI"
  }
}
```

**Implementation:**
- Looks up the session by `session_id`.
- Appends the user's response to the conversation history.
- Uses the AI agent to generate the next question or, if all fields are collected, the final structured proposal.
- Updates the session in the database.
- Returns either the next question or the completed proposal.

---

## Notes
- All endpoints return JSON.
- If a session is not found, a 404 error is returned.
- If the request body is missing the required `response` field, a 422 error is returned.
- The backend uses FastAPI, SQLModel, and pydantic_ai.Agent for AI-driven Q&A.

---

## Example Usage
1. Call `POST /start_proposal` to begin a session and get the first question.
2. Call `POST /continue_proposal/{session_id}` with the user's answer to proceed through the Q&A.
3. Repeat step 2 until the API returns a completed proposal.

---

## Future Endpoints (not implemented)
- Fetch proposal as PDF
- Update a specific section
- Regenerate or rewrite proposal with custom prompts
- List all sessions

---
