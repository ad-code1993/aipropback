# AI Proposal Generator Backend

This is a FastAPI backend for an AI-powered project proposal generator. It manages chat-based proposal sessions, stores chat history, and generates structured project proposals using an AI agent.

## Features
- Start and continue chat-based proposal sessions
- Store and retrieve chat history
- Generate structured project proposals
- Regenerate proposals with custom style/tone or prompt

## Requirements
- Python 3.9+
- SQLite (default) or other SQLModel-supported DB
- See `requirements.txt` for Python dependencies

## .env File
Create a `.env` file in the `app/` directory or project root with the following variables:

```
# Database URL (default is SQLite)
DATABASE_URL=sqlite:///app.db

# (Optional) API keys for your AI agent, if required
# OPENAI_API_KEY=your-openai-key
# ANTHROPIC_API_KEY=your-anthropic-key
```

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up the database:**
   - By default, uses SQLite (`app.db`).
   - To use another DB, update `DATABASE_URL` in `.env`.
   - Run Alembic migrations if needed:
     ```bash
     alembic upgrade head
     ```

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **API Docs:**
   Visit [http://localhost:8000/docs](http://localhost:8000/docs)

## Deployment

- **Production server:**
  - Use a production ASGI server like `gunicorn` with `uvicorn` workers:
    ```bash
    gunicorn -k uvicorn.workers.UvicornWorker app.main:app
    ```
  - Set environment variables as needed (see `.env` above).
  - Ensure your database is production-ready (not SQLite for multi-user/prod).

- **Vercel/Serverless:**
  - This project can be adapted for serverless deployment (see `vercel.json`).
  - Ensure cold start and DB connection handling is robust.

## Environment Variables
| Variable         | Description                        | Example                        |
|------------------|------------------------------------|--------------------------------|
| DATABASE_URL     | SQLModel DB connection string      | sqlite:///app.db               |
| OPENAI_API_KEY   | (Optional) OpenAI API key          | sk-...                         |
| ANTHROPIC_API_KEY| (Optional) Anthropic API key       | ...                            |

## Notes
- For production, use a secure database and manage secrets safely.
- The backend expects a compatible AI agent and prompt structure.
- See `app/api.py` for API endpoints and usage.

---

MIT License
