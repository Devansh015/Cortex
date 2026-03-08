"""
FastAPI router for the chatbot module.

Mount this in your main FastAPI app:

    from backend.chatbot.router import router as chat_router
    app.include_router(chat_router)

Endpoints
---------
  POST  /chat/{user_id}           – send a chat message, get AI reply
  GET   /chat/{user_id}/insights  – auto-generated profile insights
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .chat_service import chat_with_profile, generate_insights
from .models import ChatRequest, ChatResponse, InsightsResponse

router = APIRouter(prefix="/chat", tags=["Chatbot"])


@router.post("/{user_id}", response_model=ChatResponse)
def api_chat(user_id: str, body: ChatRequest):
    """
    Send a message grounded in the user's profile and get an AI reply.

    The request may include ``conversation_history`` for multi-turn context.
    """
    response = chat_with_profile(
        user_id=user_id,
        message=body.message,
        conversation_history=body.conversation_history,
    )
    return response


@router.get("/{user_id}/insights", response_model=InsightsResponse)
def api_insights(user_id: str):
    """
    Return auto-generated insights (strengths, growth areas, learning paths)
    derived from the user's current profile scores.
    """
    insights = generate_insights(user_id)
    return insights
