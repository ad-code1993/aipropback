from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent

# Step 1: Define proposal input model
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

sample_input = ProposalInput(
    client_name="SRH",
    project_title="SRH Project Deliverables System",
    problem_statement=(
        "SRH currently lacks a centralized system for tracking project deliverables, "
        "leading to inefficiencies in project management, communication gaps between teams, "
        "and difficulties in monitoring project progress and resource allocation."
    ),
    proposed_solution=(
        "We propose developing a custom web application that will centralize all project deliverables, "
        "provide real-time tracking and reporting, and improve team collaboration through integrated "
        "communication tools and automated notifications."
    ),
    previous_experience=(
        "Our team has successfully delivered similar project management systems for organizations "
        "in healthcare and education sectors, with demonstrated improvements in project delivery times "
        "and team productivity."
    ),
    objectives=(
        "- Centralize deliverables tracking\n"
        "- Enhance project management efficiency\n"
        "- Improve team communication and collaboration\n"
        "- Provide data-driven insights for decision making\n"
        "- Reduce project delays through proactive monitoring"
    ),
    implementation_plan=(
        "Phase 1: Requirements Gathering (2 months)\n"
        "Phase 2: Application Development (6 months)\n"
        "Phase 3: Testing & Deployment (2 months)\n"
        "Phase 4: Documentation & Training (2 months)"
    ),
    benefits=(
        "- Improved visibility into project status\n"
        "- Reduced administrative overhead\n"
        "- Better resource allocation\n"
        "- Faster identification of project risks\n"
        "- Standardized reporting across projects"
    ),
    timeline="Start Date: July 1, 2025, End Date: June 30, 2026 (1 year duration)",
    budget="Approximately $150,000 including development, testing, and first-year maintenance",
    deliverables=(
        "- Web application with all core features\n"
        "- API documentation\n"
        "- User training materials\n"
        "- Administrator guide\n"
        "- Technical documentation\n"
        "- 3 months post-launch support"
    ),
    technologies=(
        "Python/Django backend, React.js frontend, PostgreSQL database, "
        "AWS cloud hosting, Docker containers, CI/CD pipeline"
    )
)

# Step 3: Create the Gemini AI agent
agent = Agent("google-gla:gemini-2.0-flash")

# Step 4: Format prompt for proposal generation

def format_prompt(data: ProposalInput) -> str:
    return f"""
You are a professional technical writer. Write a detailed project proposal using the following structure:

# Executive Summary
Provide a concise overview of the proposal's key points, including:
- Client: {data.client_name}
- Project: {data.project_title}
- Main objectives: {data.objectives}

# Problem Statement
Clearly define the problem or opportunity:
{data.problem_statement}

# Proposed Solution
Describe the plan in detail:
{data.proposed_solution}

# Previous Experience (if applicable)
{data.previous_experience if data.previous_experience else "N/A"}

# Objectives
Outline the benefits:
{data.objectives}

# Implementation Plan
Explain how the solution will be implemented:
{data.implementation_plan}

# Benefits for the Client
Detail the positive outcomes:
{data.benefits}

# Timeline
Project schedule:
{data.timeline}

# Budget Overview
{data.budget if data.budget else "To be discussed"}

# Deliverables
{data.deliverables}

# Technologies
{data.technologies}

Write in a professional tone, using clear section headings and bullet points where appropriate.
Ensure the proposal flows logically from problem identification to solution implementation.
"""

# Step 5: Generate proposal
async def generate_proposal():
    prompt = format_prompt(sample_input)
    result = await agent.run(prompt)
    print("\n📄 Generated Proposal:\n")
    print(result.output)
