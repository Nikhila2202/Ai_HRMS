

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import get_db

from app.models.model import (
    User,
    AIConversation,
    AIMessage
)

from app.auth.dependencies import get_current_user

from app.schemas.ai_assistant import (
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
    AIChatRequest
)


# =====================================
# ROUTER
# =====================================

router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"]
)


# =====================================
# HELPER - GENERATE RULE-BASED RESPONSE
# =====================================

def generate_hr_response(message: str):

    text = message.lower()

    if "leave balance" in text:
        return (
            "I can help you check your leave balance. "
            "The leave balance integration is not connected yet."
        )

    elif "apply for leave" in text or "leave request" in text:
        return (
            "You can apply for leave through the "
            "Leave Management section."
        )

    elif "salary certificate" in text:
        return (
            "You can request a salary certificate "
            "through the HR Documents section."
        )

    elif "profile" in text:
        return (
            "You can view your employee details "
            "through the Employee Profile section."
        )

    elif "hello" in text or "hi" in text:
        return (
            "Hello! Welcome to the HR Assistant. "
            "How can I help you today?"
        )

    else:
        return (
            "Thank you for contacting the HR Assistant. "
            "I can currently help with basic HR enquiries "
            "about leave, documents and employee profiles."
        )


# =====================================
# 1. POST - CREATE CONVERSATION
# =====================================

@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    request_data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversation = AIConversation(
        user_id=current_user.user_id,
        title=request_data.title,
        status="active"
    )

    try:

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create conversation"
        )


# =====================================
# 2. GET - MY CONVERSATIONS
# =====================================

@router.get(
    "/conversations",
    response_model=list[ConversationResponse]
)
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversations = db.query(AIConversation).filter(
        AIConversation.user_id == current_user.user_id
    ).order_by(
        AIConversation.started_at.desc()
    ).all()

    return conversations


# =====================================
# 3. GET - CONVERSATION MESSAGES
# =====================================

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse]
)
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    conversation = db.query(AIConversation).filter(
        AIConversation.conversation_id == conversation_id,
        AIConversation.user_id == current_user.user_id
    ).first()

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages = db.query(AIMessage).filter(
        AIMessage.conversation_id == conversation_id
    ).order_by(
        AIMessage.created_at.asc()
    ).all()

    return messages


# =====================================
# 4. POST - AUTHENTICATED CHAT
# =====================================

@router.post("/chat")
def authenticated_chat(
    request_data: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    message = request_data.message.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    # Check conversation ownership

    conversation = db.query(AIConversation).filter(
        AIConversation.conversation_id == request_data.conversation_id,
        AIConversation.user_id == current_user.user_id
    ).first()

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    # Check conversation status

    if conversation.status != "active":

        raise HTTPException(
            status_code=400,
            detail="Conversation is not active"
        )

    try:

        # Save user message

        user_message = AIMessage(
            conversation_id=conversation.conversation_id,
            sender_type="user",
            content=message
        )

        db.add(user_message)
        db.flush()

        # Generate temporary response without LLM

        assistant_response = generate_hr_response(message)

        # Save assistant message

        assistant_message = AIMessage(
            conversation_id=conversation.conversation_id,
            sender_type="assistant",
            content=assistant_response,
            model_name=None
        )

        db.add(assistant_message)

        # Update last message time

        conversation.last_message_at = datetime.now(timezone.utc)

        db.commit()

        db.refresh(user_message)
        db.refresh(assistant_message)

        return {
            "conversation_id": conversation.conversation_id,

            "user_message": {
                "message_id": user_message.message_id,
                "sender_type": user_message.sender_type,
                "content": user_message.content,
                "created_at": user_message.created_at
            },

            "assistant_response": {
                "message_id": assistant_message.message_id,
                "sender_type": assistant_message.sender_type,
                "content": assistant_message.content,
                "created_at": assistant_message.created_at
            }
        }

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to process chat message"
        )
