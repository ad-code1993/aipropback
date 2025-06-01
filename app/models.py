from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class ProposalSession(SQLModel, table=True):
    session_id: str = Field(primary_key=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    title: str = ""
    progress: int = 0
    client_name: str = ""
    project_title: str = ""
    problem_statement: str = ""
    proposed_solution: str = ""
    previous_experience: Optional[str] = None
    objectives: str = ""
    implementation_plan: str = ""
    benefits: str = ""
    timeline: str = ""
    budget: Optional[str] = None
    deliverables: str = ""
    technologies: str = ""
    history: str = ""
    status: str = "active"
    latest_proposal: Optional[str] = Field(default=None, nullable=True)
    sections: List["ProposalSection"] = Relationship(back_populates="session")

class ProposalSection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="proposalsession.session_id")
    section_name: str
    content: str
    last_updated: datetime
    session: ProposalSession = Relationship(back_populates="sections")
