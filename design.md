# 📘 Backend Requirements: AI Proposal Generator (FastAPI)

---

## 🧱 Tech Stack Overview

| Component       | Tech Used                                 |
| --------------- | ----------------------------------------- |
| API Framework   | FastAPI                                   |
| AI Engine       | `pydantic_ai.Agent` or mock wrapper       |
| Data Models     | `pydantic.BaseModel`                      |
| Session Storage | sqilte (dev) → Redis/PostgreSQL (prod) |
| PDF Export      | `fpdf`, `reportlab`, or similar           |
| CORS            | `fastapi.middleware.cors`                 |
| Deployment      | Uvicorn + Gunicorn                        |

---

## 📌 API Endpoints & Purpose

---

### 1. `POST /start_proposal`

* **Purpose**: Starts a new interactive proposal session.
* **Returns**: `session_id`, first question
* **Internals**:

  * Creates a unique `session_id`
  * Starts a conversation with `Agent.ask(...)`
  * Stores initial state in session store

---

### 2. `POST /continue_proposal/{session_id}`

* **Purpose**: Receives a user answer and returns the next question (or full draft if completed).
* **Body**:

```json
{ "response": "We aim to automate hiring processes." }
```

* **Returns**: Next question OR completed proposal

---

### 3. `GET /proposal/{session_id}`

* **Purpose**: Fetch current structured proposal data.
* **Returns**: JSON version of `ProposalInput` model.

---

### 4. `GET /proposal/{session_id}/pdf`

* **Purpose**: Return the generated proposal as a downloadable PDF.
* **Returns**: `application/pdf` file stream.

---

### 5. `POST /proposal/{session_id}/update_section`

* **Purpose**: Regenerate a specific section using a custom prompt.
* **Body**:

```json
{
  "section": "timeline",
  "new_prompt": "Make it more concise for startup investors."
}
```

* **Returns**: Updated section text

---

### 6. `POST /proposal/{session_id}/regenerate`

* **Purpose**: Regenerates the full proposal from the same inputs, possibly with a new style.
* **Body (optional)**:

```json
{ "style": "more persuasive", "tone": "formal" }
```

* **Returns**: Full regenerated proposal

---

### 7. `POST /proposal/{session_id}/custom_prompt`

* **Purpose**: Apply a freeform prompt to regenerate the full proposal creatively.
* **Body**:

```json
{ "prompt": "Rewrite the proposal as if pitching to a government grant committee." }
```

* **Returns**: Fully rewritten proposal text

---

### 8. `GET /sessions`

* **Purpose**: Lists all active proposal sessions (for dashboard).
* **Returns**: Array of sessions (title, date, progress, etc.)

---

## 🧠 AI Agent Integration

* Use `pydantic_ai.Agent` with:

```python
chat_agent = Agent("google-gla:gemini-2.0-flash")
structured_agent = Agent("google-gla:gemini-2.0-flash", output_type=ProposalInput)
```

* Regenerate / update prompts use:

```python
await structured_agent.run({
    "input": base_data,
    "prompt": "Rewrite the timeline to be more concise..."
})
```

---

## 🧾 Pydantic Models

### `ProposalInput`

```python
class ProposalInput(BaseModel):
    client_name: str
    project_title: str
    project_goals: str
    timeline: str
    deliverables: str
    technologies: str
```

### `SectionUpdateRequest`

```python
class SectionUpdateRequest(BaseModel):
    section: str
    new_prompt: str
```

### `PromptRewriteRequest`

```python
class PromptRewriteRequest(BaseModel):
    prompt: str
```

---

## 💾 Session Management

* Sessions are stored in the database using the `ProposalSession` and `ProposalSection` tables defined in the schema.
* Each session is uniquely identified by `session_id` and contains all relevant proposal data, history, and progress.
* For development, you may use SQLite; for production, migrate to PostgreSQL or Redis as needed.

Example SQLModel usage:

```python
from sqlmodel import Session, select
from .models import ProposalSession

def get_proposal_session(db: Session, session_id: str):
    statement = select(ProposalSession).where(ProposalSession.session_id == session_id)
    return db.exec(statement).first()
```

---

## 🧩 FastAPI Setup

### Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict by domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### PDF Generation

```python
from fpdf import FPDF
def generate_pdf(proposal: ProposalInput) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for key, value in proposal.model_dump().items():
        pdf.multi_cell(0, 10, f"{key.capitalize()}: {value}\n")
    return pdf.output(dest='S').encode('latin1')
```

---

## 🧪 Testing Strategy

* ✅ Unit test for each endpoint using `TestClient`
* ✅ Mock AI Agent responses for testing
* ✅ Test PDF generation for valid schema

---

## 🛠 Optional Enhancements

| Feature               | Description                                  |
| --------------------- | -------------------------------------------- |
| WebSocket support     | For real-time AI Q\&A (if streaming enabled) |
| Admin view            | For managing user sessions & proposals       |
| Auth with JWT         | If user login is required                    |
| Persistent DB storage | PostgreSQL or MongoDB for proposal history   |

---