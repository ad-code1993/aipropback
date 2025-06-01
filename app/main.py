from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router , engine
from sqlmodel import SQLModel, create_engine
import os



app = FastAPI()

# CORS middleware (allow all for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)

# Create tables on startup
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
