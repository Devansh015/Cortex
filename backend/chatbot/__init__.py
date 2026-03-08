"""
Chatbot module – Gemini-powered conversational advisor.

Provides personalised insights, learning advice, project suggestions,
and skill-gap analysis based on the user's Knowledge Map profile.
"""

from .chat_service import chat_with_profile, generate_insights
from .models import ChatMessage, ChatRequest, ChatResponse, InsightsResponse
from .router import router as chat_router

__all__ = [
    "chat_router",
    "chat_with_profile",
    "generate_insights",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "InsightsResponse",
]
