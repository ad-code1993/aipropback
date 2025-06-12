import asyncio
import json
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
from .util import MODEL_SETTINGS, AGENT_MODEL  # Ensure this points to correct config

load_dotenv()

# ─────────────── Proposal Schema ───────────────
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

# ─────────────── Chat Output ───────────────
class chat_output(BaseModel):
    reason: str = Field(..., description="Rationale behind asking the next question")
    recommendation: Optional[str] = Field(None, description="Optional contextual suggestion to help the user make better decisions")
    question: str = Field(..., description="The actual question posed to the user")
    done: Optional[bool] = False

# ─────────────── Prompt Template ───────────────
BASE_PROMPT = """
You are a highly skilled QA chatbot, operating as a professional **Proposal Intake Agent**. Your core function is to systematically collect 12 essential structured fields required for a software project proposal. You will achieve this by engaging the user in a guided conversation, asking one precise question at a time, and offering relevant recommendations to help the user formulate comprehensive answers. Leverage the conversation history to inform your next question and recommendations.

---

## FIELDS TO COLLECT

You must obtain clear and complete answers for the following 12 fields, in this order:

1.  **client_name**: The name of the client.
2.  **project_title**: The title of the software project.
3.  **problem_statement**: The core problem or challenge the project addresses.
4.  **proposed_solution**: The proposed software solution.
5.  **previous_experience**: Any relevant prior experience.
6.  **objectives**: The key goals and desired outcomes of the project.
7.  **implementation_plan**: The strategy for executing the project.
8.  **benefits**: The advantages or positive impacts of the project.
9.  **timeline**: The project schedule with milestones.
10. **budget**: The high-level budget overview.
11. **deliverables**: The tangible outputs or results of the project.
12. **technologies**: The specific technologies to be used.

---

## RULES FOR CONVERSATION

1. Ask only one question per turn, but you may cover multiple **related fields** in one question to reduce repetition.
2. It is a must to ask at least 10 questions before concluding.
2. After each user response, intelligently extract values for one or more fields using fuzzy logic.
   (e.g. “We’ll build it in three phases” → delivery_stages is answered.)
3. Do not repeat any field that has already been answered unless a previous answer was unclear or incomplete.
4. Stop only when **all required fields have been filled**.
5. Do not say “All done” or mark the session as complete unless:
   - At least 12 questions have been asked AND
   - All 30 fields have been explicitly answered or inferred.
6. From any single user message, infer at most 3 fields. If more fields appear possible, ask a follow-up to confirm them explicitly.
7. When all fields are collected and at least 12 questions have been asked, respond with:
Reason: All fields collected.
Question: All done.
And set done=true in your output.
8. Do not exceed a reasonable number of questions (aim for 12–15 total). If needed, rephrase or group fields to clarify vague responses.
9. Do not assume any fields are filled unless explicitly provided.
10. If no conversation history exists, begin with the first unanswered field.

## OUTPUT FORMAT (MANDATORY)

Every response you generate **must** strictly adhere to the following JSON-like structure:


"Reason": "Explain why this specific question is being asked now.",
"Recommendation": "If relevant, offer a helpful suggestion to guide a better response based on past inputs. Also, suggest a possible answer based on context to help the user respond.",
"Question": "Ask exactly one field-specific question per turn.",
"Done": "Set to true only when all 12 fields are complete and confidently filled. Otherwise, set to false."

"""

# ─────────────── Agents ───────────────
chat_agent = Agent(
    model=AGENT_MODEL,
    model_settings=MODEL_SETTINGS,
    system_prompt=BASE_PROMPT,
    output_type=chat_output
)

STRUCTURED_PROMPT = """
You are a data extraction agent.

Given the following conversation history between an Assistant and a User,
extract and return a complete and valid JSON object that matches the ProposalInput schema.

Schema:
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

Only return the parsed JSON object. Do not explain or comment. Infer missing values if necessary based on context.
"""

structured_agent = Agent(
    model=AGENT_MODEL,
    model_settings=MODEL_SETTINGS,
    system_prompt=STRUCTURED_PROMPT,
    output_type=ProposalInput
)

# ─────────────── Dynamic Chat Flow ───────────────
async def dynamic_conversation():
    print("\n💬 Starting dynamic proposal Q&A (AI with reasoning)...\n")

    history = BASE_PROMPT.strip() + "\n\n"
    question_count = 0

    while True:
        response = await chat_agent.run(history)
        ai_output = response.output

        print(f"🤖 AI: {ai_output.reason}\n")
        if ai_output.recommendation:
            print(f"💡 Recommendation: {ai_output.recommendation}\n")
        print(f"❓ Question: {ai_output.question}\n")

        if ai_output.done or "all done" in ai_output.question.lower():
            break

        user_input = input("🧑 You: ").strip()
        if user_input.lower() == "exit":
            print("👋 Exiting...")
            return

        history += f"Assistant: Reason: {ai_output.reason}\nRecommendation: {ai_output.recommendation or 'None'}\nQuestion: {ai_output.question}\n"
        history += f"User: {user_input}\n"

        question_count += 1
        if question_count >= 20:
            print("🔚 Max question limit reached.\n")
            break

    print("\n🧠 Generating structured proposal...\n")
    final_result = await structured_agent.run(history)
    proposal = final_result.output

    print("✅ Final Proposal (Structured):")
    print(json.dumps(proposal.model_dump(), indent=2))

# ─────────────── CLI ───────────────
def main():
    print("🧠 Dynamic AI Proposal Generator")
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
