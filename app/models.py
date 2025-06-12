from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field as PydanticField, validator


class ProposalStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProposalSession(SQLModel, table=True):
    session_id: str = Field(primary_key=True, description="Unique identifier for the session")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    title: str = Field(max_length=255, default="", description="Title of the proposal session")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage")
    client_name: str = Field(max_length=255, default="", description="Name of the client")
    project_title: str = Field(max_length=255, default="", description="Title of the project")
    problem_statement: str = Field(default="", description="Description of the problem being addressed")
    proposed_solution: str = Field(default="", description="Proposed solution to the problem")
    previous_experience: Optional[str] = Field(default=None, description="Details of previous experience")
    objectives: str = Field(max_length=1024, default="", description="Objectives of the proposal")
    implementation_plan: str = Field(max_length=1024, default="", description="Plan for implementation")
    benefits: str = Field(max_length=1024, default="", description="Benefits of the proposal")
    timeline: str = Field(max_length=255, default="", description="Timeline for the project")
    budget: Optional[str] = Field(default=None, description="Estimated budget of the proposal")
    deliverables: str = Field(max_length=1024, default="", description="Expected deliverables")
    technologies: str = Field(max_length=512, default="", description="Technologies involved")
    status: ProposalStatus = Field(default=ProposalStatus.ACTIVE, description="Status of the proposal")
    latest_proposal: Optional[str] = Field(default=None, nullable=True, description="Latest proposal details")
    sections: List["ProposalSection"] = Relationship(back_populates="session")
    chat_history: List["ChatHistoryTable"] = Relationship(back_populates="session")

    def __repr__(self):
        return f"<ProposalSession(session_id={self.session_id}, title={self.title})>"


class ProposalSection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="Unique identifier for the section")
    session_id: str = Field(foreign_key="proposalsession.session_id", description="Associated session identifier")
    section_name: str = Field(max_length=255, description="Name of the section")
    content: str = Field(description="Content of the section")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    session: ProposalSession = Relationship(back_populates="sections")

    def __repr__(self):
        return f"<ProposalSection(id={self.id}, section_name={self.section_name})>"


class ChatHistoryTable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="Unique identifier for the chat message")
    message: str = Field(description="Content of the message")
    role: str = Field(default="user", max_length=32, description="Role of the sender (user, assistant, system)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the message")
    session_id: str = Field(foreign_key="proposalsession.session_id", description="Associated session identifier")
    session: ProposalSession = Relationship(back_populates="chat_history")

    def __repr__(self):
        return f"<ChatHistoryTable(id={self.id}, role={self.role}, timestamp={self.timestamp})>"