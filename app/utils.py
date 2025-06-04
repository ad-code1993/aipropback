import asyncio
import json
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
from .util import MODEL_SETTINGS, AGENT_MODEL

load_dotenv()
# Agent configuration


# Proposal schema
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

class chat_output(BaseModel):
    reason: str = Field(..., description="Reasoning behind the question asked by the AI")
    question: str = Field(..., description="The question asked by the AI")
    done: Optional[bool] = False

BASE_PROMPT = """
You are a helpful assistant collecting information to build a complete software project proposal.

For each field below, ask the user a specific question. **For every question you ask, include a brief one-line reasoning** about why that information is important:

- client_name
- project_title
- problem_statement
- proposed_solution
- previous_experience
- objectives
- implementation_plan
- benefits
- timeline
- budget
- deliverables
- technologies

Do not generate a final proposal yet. Ask only one question at a time.
Format your message as:
"Reason: <reason>. \nQuestion: <your question here>"

If all fields are collected, say "All done" and stop asking.
"""

# Agents
chat_agent = Agent(AGENT_MODEL, model_settings=MODEL_SETTINGS, system_prompt= BASE_PROMPT, output_type=chat_output)
structured_agent = Agent(AGENT_MODEL, model_settings=MODEL_SETTINGS, output_type=ProposalInput)

# Instruction with reasoning mode

async def dynamic_conversation():
    print("\n💬 Starting dynamic proposal Q&A (AI with reasoning)...\n")

    history = BASE_PROMPT.strip() + "\n\n"
    collected = {}

    while True:
        response = await chat_agent.run(history)
        full_reply = response.output.question.strip()

        if "all done" in full_reply.lower():
            break

        # Extract and show reasoned question
        print(f"🤖 AI: {full_reply}")
        user_input = input("🧑 You: ").strip()

        if user_input.lower() == "exit":
            print("👋 Exiting...")
            return

        history += f"Assistant: {full_reply}\nUser: {user_input}\n"

        # Optional heuristic to stop if all fields likely answered
        if len(collected) >= 6:
            break

    # Final structured result
    print("\n🧠 Generating structured proposal...\n")
    final_result = await structured_agent.run(history)
    proposal = final_result.output

    print("✅ Final Proposal (Structured):")
    print(json.dumps(proposal.model_dump(), indent=2))

def main():
    print("🧠 Dynamic AI Proposal Generator (Gemini-powered)")
    print(" 1: Start AI-guided Proposal Collection")
    print(" 0: Exit")

    while True:
        choice = input("Select option (0 or 1): ").strip()
        if choice == "1":
            asyncio.run(dynamic_conversation())
        elif choice == "0":
            print("👋 Goodbye!")
            break
        else:
            print("⚠️ Invalid option. Please enter 0 or 1.")

if __name__ == "__main__":
    main()
