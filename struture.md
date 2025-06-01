# 🗂️ Project Structure: AI Proposal Generator Backend

```
backend/
│
├── database.md         # Database schema and migration instructions
├── design.md           # System and API design documentation
├── requirements.txt    # Python dependencies
├── struture.md         # (This file) Project structure overview
│
├── app/                # Main FastAPI application code
│   ├── __init__.py
│   ├── main.py         # FastAPI app entrypoint
│   ├── models.py       # SQLModel classes (database tables)
│   ├── schemas.py      # Pydantic models (API request/response)
│   ├── crud.py         # Database CRUD operations
│   ├── api.py          # API route definitions (APIRouter)
│   └── utils.py        # Utility functions (PDF, AI, etc.)
│
├── alembic/            # Alembic migrations (after init)
│
└── tests/              # Unit and integration tests
    └── test_api.py
```

- Place all FastAPI and SQLModel code in the `app/` directory for clarity and scalability.
- Use `alembic/` for database migrations.
- Keep documentation and requirements in the project root.
- Add or remove files/folders as your project grows.
