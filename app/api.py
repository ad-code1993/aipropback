from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select, create_engine, Field
from .models import ProposalSession
from .utils import chat_agent, structured_agent, ProposalInput as ProposalInputModel, BASE_PROMPT
from .util import agent as proposal_agent, ProposalInput
import uuid
import os
import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv  
import logging
from .models import ChatHistoryTable, ProposalStatus
from .service import chat_history_to_model_messages, ChatMessage, ChatHistory
from pydantic import BaseModel
    

load_dotenv()  # Load environment variables from .env file
# Set up the engine here (since app.main is not guaranteed to have it)
DATABASE_URL = os.getenv("DATABASE_URL", "")  # Default to SQLite for testing
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

class ContinueProposalRequest(BaseModel):
    response: str

# 1. Start proposal session
@router.post("/start_proposal")
async def start_proposal(db: Session = Depends(get_session)):
    session_id = str(uuid.uuid4())
    # Pass BASE_PROMPT as the initial prompt to the agent
    ai_response = await chat_agent.run(BASE_PROMPT)
    if not ai_response or not getattr(ai_response, "output", None):
        raise HTTPException(status_code=500, detail="Failed to get initial AI response")
    reason = getattr(ai_response.output, "reason", "").strip()
    first_question = getattr(ai_response.output, "question", "").strip()
    recommendation = getattr(ai_response.output, "recommendation", "")
    if recommendation:
        recommendation = recommendation.strip()

    # Create the proposal session with default values
    proposal_session = ProposalSession(
        session_id=session_id,
        # created_at and updated_at use default_factory
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
        status=ProposalStatus.ACTIVE,
        latest_proposal=None,
    )
    db.add(proposal_session)
    db.commit()
    db.refresh(proposal_session)

    # Add the first assistant message to chat history (explicit role)
    chat_entry = ChatHistoryTable(
        message=first_question,
        session_id=session_id,
        role="assistant"
    )
    db.add(chat_entry)
    db.commit()

    return {
        "session_id": session_id,
        "question": first_question,
        "reason": reason,
        "recommendation": recommendation
    }

# 2. Continue proposal Q&A with simulated streaming
@router.post("/continue_proposal/{session_id}")
async def continue_proposal(
    session_id: str,
    body: ContinueProposalRequest,
    db: Session = Depends(get_session),
):
    try:
        logging.info(f"📨 Incoming /continue_proposal for session_id={session_id} | body={body}")

        # 1. Validate session
        session = db.exec(
            select(ProposalSession).where(ProposalSession.session_id == session_id)
        ).first()
        if not session:
            logging.warning(f"⚠️ Session {session_id} not found.")
            raise HTTPException(status_code=404, detail="Session not found")

        # 2. Extract and validate user response
        user_response = body.response
        if not user_response:
            logging.warning("⚠️ Missing 'response' in request body")
            raise HTTPException(status_code=422, detail="Missing 'response' in request body")

        # 3. Save user message to chat history (explicit role)
        db.add(ChatHistoryTable(message=user_response, session_id=session_id, role="user"))
        db.commit()

        # 4. Reconstruct chat history into ChatHistory model
        chat_entries = db.exec(
            select(ChatHistoryTable)
            .where(ChatHistoryTable.session_id == session_id)
            .order_by(ChatHistoryTable.__table__.c.id)
        ).all()

        # Use stored roles
        chat_messages = [ChatMessage(role=entry.role, message=entry.message) for entry in chat_entries]
        chat_history = ChatHistory(history=chat_messages)
        model_messages = chat_history_to_model_messages(chat_history)

        # Print the chat history as a formatted string (for API or debugging)
        data = BASE_PROMPT + "\n\n" + "\n".join(
            f"[{msg.role.upper()}] {msg.message}" for msg in chat_messages
        )
        

        # 5. Get AI response based on structured message history
        # Always pass the full message history and an empty string as the first argument
        ai_response = await chat_agent.run( data , message_history=model_messages)
        logging.info(f"AI response from chat_agent.run: {ai_response}")
        output = getattr(ai_response, "output", None)
        if not output:
            raise HTTPException(status_code=500, detail="AI output is missing")

        # 6. Extract AI response data
        next_question = getattr(output, "question", "").strip()
        reasoning = getattr(output, "reason", "").strip()
        recommendation = getattr(output, "recommendation", "")
        done = getattr(output, "done", False)
        logging.info(f"AI output fields: done={done}, question={next_question}, reason={reasoning}, recommendation={recommendation}")
        logging.info(f"Raw AI output: {output}")

        # 7. Save assistant response (explicit role)
        db.add(ChatHistoryTable(message=next_question, session_id=session_id, role="assistant"))
        db.commit()
        logging.info(f"Assistant response added to chat history: {next_question}")

        # 8. If done, extract and update structured proposal
        if done or "all done" in next_question.lower() or reasoning.lower() == "all fields have been successfully collected.":
            try:
                structured_result = await structured_agent.run(message_history=model_messages)
                proposal_data = structured_result.output

                for field in [
                    "client_name", "project_title", "problem_statement", "proposed_solution",
                    "previous_experience", "objectives", "implementation_plan",
                    "benefits", "timeline", "budget", "deliverables", "technologies"
                ]:
                    setattr(session, field, getattr(proposal_data, field, None))

                db.add(session)
                db.commit()
                db.refresh(session)

                logging.info(f"✅ Structured proposal saved for session {session_id}")

            except Exception as extract_exc:
                logging.error(f"❌ Failed to extract structured proposal: {extract_exc}")

        # 9. Construct final response
        response_parts = [f"[REASONING]\n{reasoning}"]
        if recommendation:
            response_parts.append(f"\n[RECOMMENDATION]\n{recommendation}")
        response_parts.append(f"\n{next_question}")
        return PlainTextResponse("\n\n".join(response_parts))

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"💥 Unexpected error in /continue_proposal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

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


