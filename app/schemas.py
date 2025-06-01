from typing import Optional
from pydantic import BaseModel, Field

class ProposalInput(BaseModel):
    client_name: str = Field(..., description="Client's name or organization")
    project_title: str = Field(..., description="Title of the project")
    problem_statement: str = Field(..., description="The problem or opportunity being addressed")
    proposed_solution: str = Field(..., description="Detailed description of the proposed solution")
    previous_experience: Optional[str] = Field(None, description="Relevant previous projects or experience")
    objectives: str = Field(..., description="Benefits and objectives of the solution")
    implementation_plan: str = Field(..., description="How the solution will be implemented")
    benefits: str = Field(..., description="Advantages for the recipient")
    timeline: str = Field(..., description="Project schedule with milestones")
    budget: Optional[str] = Field(None, description="High-level budget overview")
    deliverables: str = Field(..., description="What will be delivered")
    technologies: str = Field(..., description="Technologies to be used")
