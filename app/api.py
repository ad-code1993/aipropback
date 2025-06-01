from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, create_engine, Field
from .models import ProposalSession
from .utils import chat_agent, structured_agent, ProposalInput as ProposalInputModel, BASE_PROMPT
from .util import agent as proposal_agent, ProposalInput
import uuid
import os
import asyncio
from typing import AsyncGenerator

# Set up the engine here (since app.main is not guaranteed to have it)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
engine = create_engine(DATABASE_URL, echo=True)

# Dependency to get DB session
def get_session():
    with Session(engine) as session:
        yield session

router = APIRouter()

# Add latest_proposal to ProposalSession if not present
def ensure_latest_proposal_column():
    if not hasattr(ProposalSession, 'latest_proposal'):
        ProposalSession.latest_proposal = Field(default=None, nullable=True)

ensure_latest_proposal_column()

# Helper to format proposal prompt
def format_full_proposal_prompt(data, extra_prompt=None):
    base = f"""
You are a professional technical writer.\n\nWrite a detailed project proposal using the following structure:\n\n# Executive Summary\nProvide a concise overview of the proposal's key points, including:\n- Client: {data.get('client_name', '')}\n- Project: {data.get('project_title', '')}\n- Main objectives: {data.get('objectives', '')}\n\n# Problem Statement\nClearly define the problem or opportunity:\n{data.get('problem_statement', '')}\n\n# Proposed Solution\nDescribe the plan in detail:\n{data.get('proposed_solution', '')}\n\n# Previous Experience (if applicable)\n{data.get('previous_experience', 'N/A')}\n\n# Objectives\nOutline the benefits:\n{data.get('objectives', '')}\n\n# Implementation Plan\nExplain how the solution will be implemented:\n{data.get('implementation_plan', '')}\n\n# Benefits for the Client\nDetail the positive outcomes:\n{data.get('benefits', '')}\n\n# Timeline\nProject schedule:\n{data.get('timeline', '')}\n\n# Budget Overview\n{data.get('budget', 'To be discussed')}\n\n# Deliverables\n{data.get('deliverables', '')}\n\n# Technologies\n{data.get('technologies', '')}\n"""
    if extra_prompt:
        base += f"\n{extra_prompt}\n"
    base += "\nWrite in a professional tone, using clear section headings and bullet points where appropriate.\nEnsure the proposal flows logically from problem identification to solution implementation."
    return base

# 1. Start proposal session
@router.post("/start_proposal")
async def start_proposal(db: Session = Depends(get_session)):
    session_id = str(uuid.uuid4())
    ai_response = await chat_agent.run(BASE_PROMPT.strip())
    if not ai_response or not getattr(ai_response, "output", None):
        raise HTTPException(status_code=500, detail="Failed to get initial AI response")
    reason = ai_response.output.reason.strip()
    first_question = ai_response.output.question.strip()
    # Initialize history with BASE_PROMPT and the first question
    history = f"{BASE_PROMPT.strip()}\n\n### Assistant:\n{first_question}"
    proposal_session = ProposalSession(
        session_id=session_id,
        created_at=None,
        updated_at=None,
        title="",
        progress=0,
        client_name="",
        project_title="",
        problem_statement="",
        proposed_solution="",
        previous_experience=None,
        objectives="",
        implementation_plan="",
        benefits="",
        timeline="",
        budget=None,
        deliverables="",
        technologies="",
        history=history,
        status="active"
    )
    db.add(proposal_session)
    db.commit()
    db.refresh(proposal_session)
    return {"session_id": session_id, "question": first_question, "reason": reason}

# 2. Continue proposal Q&A with simulated streaming
@router.post("/continue_proposal/{session_id}")
async def continue_proposal(session_id: str, body: dict, db: Session = Depends(get_session)):
    session = db.exec(select(ProposalSession).where(ProposalSession.session_id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    user_response = body.get("response")
    if not user_response:
        raise HTTPException(status_code=422, detail="Missing 'response' in request body")
    # Update session with user response (structured)
    session.history += f"\n\n### User:\n{user_response}\n"
    db.add(session)
    db.commit()
    db.refresh(session)

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            ai_response = await chat_agent.run(session.history)
        except Exception:
            yield "[ERROR] Failed to get AI response."
            return
        if not ai_response or not getattr(ai_response, "output", None):
            yield "[ERROR] Failed to get AI response."
            return
        next_question = ai_response.output.question.strip()
        reasoning = ai_response.output.reason.strip()
        done_flag = getattr(ai_response.output, "done", False)
        # Stream UI output only
        streamed_output = f"[REASONING]\n{reasoning}\n\n{next_question}"
        for char in streamed_output:
            yield char
            await asyncio.sleep(0.01)
        # Store clean history (no UI markup)
        session.history += f"\n\n### Assistant:\n{reasoning}\n\n### Assistant:\n{next_question}"
        db.add(session)
        db.commit()
        db.refresh(session)
        # Check for completion
        if done_flag or "all done" in next_question.lower() or "all fields are collected" in next_question.lower():
            try:
                final_result = await structured_agent.run(session.history)
            except Exception:
                yield "[ERROR] Failed to get structured proposal."
                return
            proposal = final_result.output
            session.client_name = proposal.client_name
            session.project_title = proposal.project_title
            session.problem_statement = proposal.problem_statement
            session.proposed_solution = proposal.proposed_solution
            session.previous_experience = proposal.previous_experience
            session.objectives = proposal.objectives
            session.implementation_plan = proposal.implementation_plan
            session.benefits = proposal.benefits
            session.timeline = proposal.timeline
            session.budget = proposal.budget
            session.deliverables = proposal.deliverables
            session.technologies = proposal.technologies
            db.add(session)
            db.commit()
            db.refresh(session)
            completion_msg = f"\n[SYSTEM] Proposal generation complete! Visit the preview page.\n\n[FINAL REASONING]\n{reasoning}\n"
            for char in completion_msg:
                yield char
                await asyncio.sleep(0.01)
    return StreamingResponse(generate_stream(), media_type="text/plain")

# 3. Get proposal data
@router.get("/proposal/{session_id}", response_model=ProposalInputModel)
def get_proposal(session_id: str, db: Session = Depends(get_session)):
    session = db.exec(select(ProposalSession).where(ProposalSession.session_id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ProposalInputModel(
        client_name=session.client_name,
        project_title=session.project_title,
        problem_statement=session.problem_statement,
        proposed_solution=session.proposed_solution,
        previous_experience=session.previous_experience,
        objectives=session.objectives,
        implementation_plan=session.implementation_plan,
        benefits=session.benefits,
        timeline=session.timeline,
        budget=session.budget,
        deliverables=session.deliverables,
        technologies=session.technologies
    )

# 4. Regenerate full proposal with optional style/tone
@router.post("/proposal/{session_id}/generate")
async def regenerate_proposal(session_id: str, body: dict = Body(default={}), db: Session = Depends(get_session)):
    session = db.exec(select(ProposalSession).where(ProposalSession.session_id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    base_data = {
        "client_name": session.client_name,
        "project_title": session.project_title,
        "problem_statement": session.problem_statement,
        "proposed_solution": session.proposed_solution,
        "previous_experience": session.previous_experience,
        "objectives": session.objectives,
        "implementation_plan": session.implementation_plan,
        "benefits": session.benefits,
        "timeline": session.timeline,
        "budget": session.budget,
        "deliverables": session.deliverables,
        "technologies": session.technologies
    }
    style = body.get("style")
    tone = body.get("tone")
    extra = ""
    if style:
        extra += f"Style: {style}. "
    if tone:
        extra += f"Tone: {tone}."
    prompt = format_full_proposal_prompt(base_data, extra)
    result = await proposal_agent.run(prompt)
    proposal_text = result.output
    # Save the regenerated proposal text to the session (as latest_proposal)
    setattr(session, 'latest_proposal', proposal_text)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"proposal": proposal_text}

# New endpoint: Get the most recently generated proposal
@router.get("/proposal/{session_id}/latest")
def get_latest_proposal(session_id: str, db: Session = Depends(get_session)):
    session = db.exec(select(ProposalSession).where(ProposalSession.session_id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    latest_proposal = getattr(session, 'latest_proposal', None)
    if not latest_proposal:
        raise HTTPException(status_code=404, detail="No generated proposal found for this session")
    return {"proposal": latest_proposal}

# 5. Regenerate full proposal with a custom freeform prompt
@router.post("/proposal/{session_id}/custom_prompt")
async def custom_prompt_proposal(session_id: str, body: dict, db: Session = Depends(get_session)):
    session = db.exec(select(ProposalSession).where(ProposalSession.session_id == session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    prompt_text = body.get("prompt")
    if not prompt_text:
        raise HTTPException(status_code=422, detail="Missing 'prompt' in request body")
    base_data = {
        "client_name": session.client_name,
        "project_title": session.project_title,
        "problem_statement": session.problem_statement,
        "proposed_solution": session.proposed_solution,
        "previous_experience": session.previous_experience,
        "objectives": session.objectives,
        "implementation_plan": session.implementation_plan,
        "benefits": session.benefits,
        "timeline": session.timeline,
        "budget": session.budget,
        "deliverables": session.deliverables,
        "technologies": session.technologies
    }
    prompt = format_full_proposal_prompt(base_data, prompt_text)
    result = await proposal_agent.run(prompt)
    proposal_text = result.output
    return {"proposal": proposal_text}


