"""
Pydantic models for the chatbot module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ChatRequest(BaseModel):
    """Incoming chat request from the frontend."""

    message: str = Field(..., min_length=1, description="User message text")
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages for context continuity",
    )


class ChatResponse(BaseModel):
    """Response from the chatbot."""

    reply: str
    suggestions: List[str] = Field(
        default_factory=list,
        description="Follow-up question suggestions",
    )


class InsightItem(BaseModel):
    """A single insight about the user's profile."""

    category: str = Field(..., description="Category group or key")
    title: str
    detail: str
    score: float = Field(ge=0.0, le=1.0)


class InsightsResponse(BaseModel):
    """Auto-generated insights from the user's current profile."""

    strengths: List[InsightItem] = Field(default_factory=list)
    growth_areas: List[InsightItem] = Field(default_factory=list)
    learning_paths: List[str] = Field(default_factory=list)
    summary: str = ""
