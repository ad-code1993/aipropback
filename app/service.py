from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart, ModelMessage
from pydantic_ai.messages import ModelMessagesTypeAdapter
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender (e.g., 'user', 'assistant')")
    message: str = Field(..., description="Content of the message")

# Define a model to hold the chat history
class ChatHistory(BaseModel):
    history: List[ChatMessage] = Field(..., description="List of chat messages for the session")



def chat_message_to_model_message(msg: ChatMessage) -> ModelMessage:
    timestamp = getattr(msg, 'timestamp', datetime.now(tz=timezone.utc))
    if msg.role == 'user':
        return ModelRequest(parts=[UserPromptPart(content=msg.message, timestamp=timestamp)])
    elif msg.role == 'assistant':
        return ModelResponse(parts=[TextPart(content=msg.message)], timestamp=timestamp)
    else:
        raise ValueError(f"Unsupported role: {msg.role}")

def ensure_user_message_in_history(history: ChatHistory) -> ChatHistory:
    # Check if there is at least one user message
    if any(msg.role == 'user' for msg in history.history):
        return history
    # If not, add a default user message
    default_msg = ChatMessage(role='user', message="Hello, let's start the proposal.")
    return ChatHistory(history=[default_msg] + history.history)


def chat_history_to_model_messages(history: ChatHistory) -> List[ModelMessage]:
    history = ensure_user_message_in_history(history)
    if not history.history:
        raise ValueError("Chat history is empty. At least one message is required.")
    return [chat_message_to_model_message(msg) for msg in history.history]

def serialize_model_messages(messages: List[ModelMessage]) -> str:
    """Serialize model messages to JSON string for storage or transfer."""
    from pydantic_core import to_jsonable_python
    as_python_objects = to_jsonable_python(messages)
    return ModelMessagesTypeAdapter.dump_json(as_python_objects).decode()


def deserialize_model_messages(json_str: str) -> List[ModelMessage]:
    """Deserialize JSON string back to model messages."""
    return ModelMessagesTypeAdapter.validate_json(json_str)

def chat_entries_to_messages(chat_entries):
    """Convert a list of chat entries to alternating role messages for AI agent."""
    chat_messages = []
    for idx, entry in enumerate(chat_entries):
        role = "assistant" if idx % 2 == 0 else "user"
        chat_messages.append({"role": role, "content": entry.message})
    return chat_messages