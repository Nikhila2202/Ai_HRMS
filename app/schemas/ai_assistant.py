from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    user_id: int
    title: Optional[str] = None
    status: str
    started_at: datetime
    last_message_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: int
    conversation_id: int
    sender_type: str
    content: str
    model_name: Optional[str] = None
    token_count: Optional[int] = None
    created_at: datetime


class AIChatRequest(BaseModel):
    conversation_id: int
    message: str = Field(min_length=1, max_length=10000)