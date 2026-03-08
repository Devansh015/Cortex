"""
Chatbot service – Gemini-powered conversational advisor.

Uses the user's profile scores + category metadata to provide
personalised insights, learning advice, project suggestions,
and skill-gap analysis through natural conversation.

Environment
-----------
  GOOGLE_CLOUD_CONSOLE_API_KEY – same key as the scorer
  GEMINI_MODEL                 – defaults to "gemini-2.0-flash"
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from backend.profile_scoring.categories import (
    CATEGORY_GROUPS,
    CATEGORY_KEYS,
    CATEGORY_MAP,
)
from backend.profile_scoring.models import UserProfile
from backend.profile_scoring.profile_manager import (
    get_upload_history,
    get_user_profile,
)

from .models import (
    ChatMessage,
    ChatResponse,
    InsightItem,
    InsightsResponse,
)

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

GEMINI_API_KEY: str = os.getenv("GOOGLE_CLOUD_CONSOLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


# ────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────

# ── Proficiency tiers ──────────────────────────────────────
#  Maps a 0-1 score to a human-readable tier label.
#  These tiers are injected into the system prompt so Gemini
#  uses meaningful language instead of raw decimals.

_TIERS = [
    (0.00, "Unassessed"),       # exactly 0 — no evidence yet
    (0.15, "Novice"),           # 0.01 – 0.15  — minimal exposure
    (0.35, "Beginner"),         # 0.16 – 0.35  — some familiarity
    (0.55, "Intermediate"),     # 0.36 – 0.55  — working knowledge
    (0.75, "Proficient"),       # 0.56 – 0.75  — solid competence
    (0.90, "Advanced"),         # 0.76 – 0.90  — strong expertise
    (1.01, "Expert"),           # 0.91 – 1.00  — exceptional mastery
]


def _tier_label(score: float) -> str:
    """Return the qualitative tier name for a numeric score."""
    if score == 0.0:
        return "Unassessed"
    for threshold, label in _TIERS:
        if score <= threshold:
            return label
    return "Expert"


def _profile_snapshot(profile: UserProfile) -> str:
    """Build a concise textual summary of a user's profile for the prompt."""
    lines: List[str] = []

    # Group scores by region
    groups: Dict[str, List[tuple]] = {}
    for key in CATEGORY_KEYS:
        group = CATEGORY_GROUPS[key]
        score = round(profile.category_scores.get(key, 0.0), 3)
        tier = _tier_label(score)
        groups.setdefault(group, []).append(
            (CATEGORY_MAP[key], score, tier)
        )

    for group_name, cats in groups.items():
        avg = sum(s for _, s, _ in cats) / len(cats) if cats else 0.0
        region_tier = _tier_label(avg)
        cat_details = ", ".join(
            f"{name}={score} [{tier}]" for name, score, tier in cats
        )
        lines.append(
            f"  {group_name} (avg {avg:.2f} [{region_tier}]): {cat_details}"
        )

    top = profile.get_top_categories(5)
    top_str = ", ".join(
        f"{t['category']}={t['score']} [{_tier_label(t['score'])}]"
        for t in top
    )

    return (
        f"Upload count: {profile.upload_count}\n"
        f"Top-5: {top_str}\n"
        f"Scores by region:\n" + "\n".join(lines)
    )


def _build_system_prompt(profile: UserProfile) -> str:
    """Construct the system prompt that grounds the chatbot in the user's data."""
    snapshot = _profile_snapshot(profile)

    return f"""You are **Lumas**, a friendly and knowledgeable CS learning advisor.

You have access to the user's Knowledge Map – a living profile of their
technical skills across {len(CATEGORY_KEYS)} categories grouped into 9 regions
(Fundamentals, OOP, Data Structures, Algorithms, Systems, Frontend,
Dev Practices, Product, Hackathon).

─── PROFICIENCY RUBRIC ───
Each category has a score from 0.0 to 1.0.  Use the tier labels below
when describing the user's abilities — never just quote a raw number.

  0.00           → **Unassessed**  — no evidence uploaded yet; do NOT
                    assume the user is weak here, they simply haven't
                    shown this skill yet.
  0.01 – 0.15    → **Novice**      — minimal exposure; just getting started.
  0.16 – 0.35    → **Beginner**    — some familiarity; understands basics
                    but needs guided practice.
  0.36 – 0.55    → **Intermediate** — working knowledge; can apply concepts
                    in small projects with occasional guidance.
  0.56 – 0.75    → **Proficient**  — solid competence; can work independently
                    and tackle moderately complex problems.
  0.76 – 0.90    → **Advanced**    — strong expertise; comfortable with
                    edge-cases, optimisation, and mentoring others.
  0.91 – 1.00    → **Expert**      — exceptional mastery; deep understanding,
                    can architect solutions and contribute to the field.
───────────────────────────

─── CURRENT PROFILE ───
{snapshot}
────────────────────────

Guidelines:
1. **Be encouraging** – celebrate strengths before pointing out gaps.
2. **Use tier names** – say "you're at a *Proficient* level in Sorting"
   rather than "your Sorting score is 0.62".  You may mention the
   numeric score in parentheses for precision, but lead with the tier.
3. **Be specific** – reference actual category names and regions.
4. **Suggest concrete next steps** – courses, projects, exercises.
5. **Stay concise** – prefer short paragraphs and bullet points.
6. **If the user asks about something outside CS**, gently redirect.
7. When the user has very few uploads, acknowledge that the profile is
   still forming and recommend uploading more content for better insights.
8. For **Unassessed** categories, say the skill hasn't been evaluated yet
   rather than calling it a weakness.
9. You may use Markdown formatting in your replies.
"""


# ────────────────────────────────────────────────────────────
#  Chat
# ────────────────────────────────────────────────────────────

def chat_with_profile(
    user_id: str,
    message: str,
    conversation_history: Optional[List[ChatMessage]] = None,
) -> ChatResponse:
    """
    Send a user message to Gemini, grounded in the user's profile.

    Parameters
    ----------
    user_id : str
        The profile to load context from.
    message : str
        The latest user message.
    conversation_history : list[ChatMessage], optional
        Prior turns for multi-turn context.

    Returns
    -------
    ChatResponse with reply text and follow-up suggestions.
    """
    from google import genai

    profile = get_user_profile(user_id)
    if profile is None:
        return ChatResponse(
            reply="I don't have a profile for you yet. Please upload some content first so I can learn about your skills!",
            suggestions=[
                "How do I upload a GitHub repo?",
                "What kind of content can I upload?",
            ],
        )

    system_prompt = _build_system_prompt(profile)

    # Build Gemini contents list (multi-turn)
    contents: list = []
    if conversation_history:
        for msg in conversation_history[-10:]:  # keep last 10 turns
            role = "user" if msg.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

    # Append the new user message
    contents.append({"role": "user", "parts": [{"text": message}]})

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7,
                "max_output_tokens": 1024,
            },
        )
        reply_text = response.text or "I'm sorry, I couldn't generate a response."
    except Exception as exc:
        logger.error("Gemini chat error: %s", exc)
        reply_text = (
            "I'm having trouble connecting to my AI backend right now. "
            "Please try again in a moment."
        )

    # Generate follow-up suggestions based on context
    suggestions = _generate_suggestions(profile, message)

    return ChatResponse(reply=reply_text, suggestions=suggestions)


def _generate_suggestions(profile: UserProfile, last_message: str) -> List[str]:
    """Return 2-3 contextual follow-up suggestions."""
    suggestions: List[str] = []

    top = profile.get_top_categories(3)
    top_names = [t["category"] for t in top]

    # Always offer these if the profile is thin
    if profile.upload_count < 3:
        suggestions.append("What should I upload next to improve my profile?")

    # Suggest exploring strengths
    if top and top[0]["score"] > 0.1:
        suggestions.append(f"What projects can I build with my {CATEGORY_MAP.get(top_names[0], top_names[0])} skills?")

    # Suggest growth areas
    weak = sorted(
        profile.category_scores.items(), key=lambda kv: kv[1]
    )
    nonzero_weak = [(k, v) for k, v in weak if v > 0.0]
    if nonzero_weak:
        weakest_name = CATEGORY_MAP.get(nonzero_weak[0][0], nonzero_weak[0][0])
        suggestions.append(f"How can I improve my {weakest_name} skills?")
    else:
        suggestions.append("What are the most important CS topics to learn first?")

    return suggestions[:3]


# ────────────────────────────────────────────────────────────
#  Auto-generated Insights
# ────────────────────────────────────────────────────────────

def generate_insights(user_id: str) -> InsightsResponse:
    """
    Analyse the user's profile and return structured insights
    without requiring a chat message.
    """
    profile = get_user_profile(user_id)
    if profile is None:
        return InsightsResponse(
            summary="No profile found. Upload some content to get started!"
        )

    scores = profile.category_scores

    # ── Strengths (top categories with score > 0.1) ────────
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    strengths: List[InsightItem] = []
    for key, score in ranked:
        if score < 0.1 or len(strengths) >= 5:
            break
        tier = _tier_label(score)
        strengths.append(InsightItem(
            category=CATEGORY_GROUPS.get(key, "General"),
            title=CATEGORY_MAP.get(key, key),
            detail=f"{tier} ({score:.2f}) — you've shown solid evidence in this area.",
            score=score,
        ))

    # ── Growth areas (lowest non-zero or zero with related strengths) ──
    growth_areas: List[InsightItem] = []
    # Find groups where user has *some* evidence but gaps remain
    group_scores: Dict[str, List[float]] = {}
    for key in CATEGORY_KEYS:
        g = CATEGORY_GROUPS[key]
        group_scores.setdefault(g, []).append(scores.get(key, 0.0))

    for g, g_scores in group_scores.items():
        avg = sum(g_scores) / len(g_scores) if g_scores else 0.0
        tier = _tier_label(avg)
        if 0.0 < avg < 0.4:
            growth_areas.append(InsightItem(
                category=g,
                title=f"Grow your {g} skills",
                detail=(
                    f"Currently at {tier} level (avg {avg:.2f}). "
                    "Consider focused practice or a project in this area."
                ),
                score=round(avg, 3),
            ))

    # ── Learning paths ────────────────────────────────────
    learning_paths: List[str] = []
    # Suggest path based on weakest group that has any evidence
    sorted_groups = sorted(
        ((g, sum(s) / len(s)) for g, s in group_scores.items()),
        key=lambda x: x[1],
    )
    for g_name, g_avg in sorted_groups[:3]:
        tier = _tier_label(g_avg)
        if g_avg < 0.3:
            learning_paths.append(
                f"📚 {g_name} ({tier}): Start with fundamentals, then build a small project."
            )
        elif g_avg < 0.6:
            learning_paths.append(
                f"🚀 {g_name} ({tier}): You have a foundation — try intermediate challenges or contribute to open source."
            )

    if not learning_paths:
        learning_paths.append(
            "🎯 Upload more content to unlock personalised learning paths!"
        )

    # ── Summary ────────────────────────────────────────────
    strength_names = [s.title for s in strengths[:3]]
    summary = (
        f"Based on {profile.upload_count} upload(s), "
        f"your strongest areas are: {', '.join(strength_names) if strength_names else 'still forming'}. "
        f"Keep uploading repos and documents to refine your Knowledge Map!"
    )

    return InsightsResponse(
        strengths=strengths,
        growth_areas=growth_areas,
        learning_paths=learning_paths,
        summary=summary,
    )
