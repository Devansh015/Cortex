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

try:
    from ..profile_scoring.categories import (
        CATEGORY_GROUPS,
        CATEGORY_KEYS,
        CATEGORY_MAP,
    )
    from ..profile_scoring.models import UserProfile
    from ..profile_scoring.profile_manager import (
        get_upload_history,
        get_user_profile,
    )
except ImportError:
    from profile_scoring.categories import (
        CATEGORY_GROUPS,
        CATEGORY_KEYS,
        CATEGORY_MAP,
    )
    from profile_scoring.models import UserProfile
    from profile_scoring.profile_manager import (
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
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
except ImportError:
    pass

logger = logging.getLogger(__name__)

api_key = os.getenv("GOOGLE_CLOUD_CONSOLE_API_KEY", "")
model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

_IMPROVEMENT_KEYWORDS = (
    "improve",
    "improvement",
    "better",
    "weakness",
    "weaknesses",
    "gap",
    "gaps",
    "grow",
    "stronger",
    "work on",
    "focus on",
    "need to learn",
    "what should i learn",
    "where can i improve",
    "how can i improve",
    "what can i improve",
    "areas to improve",
)

_GROUP_GROWTH_RECOMMENDATIONS = {
    "Fundamentals": ("data_structures", "algorithms", "testing"),
    "OOP": ("testing", "system_design", "documentation"),
    "Data Structures": ("algorithms", "time_complexity", "testing"),
    "Algorithms": ("data_structures", "time_complexity", "testing"),
    "Systems": ("databases", "testing", "system_design"),
    "Frontend": ("responsive_design", "testing", "documentation"),
    "Dev Practices": ("testing", "ci_cd", "documentation"),
    "Product": ("system_design", "documentation", "testing"),
    "Hackathon": ("integrations", "system_design", "testing"),
}

_CATEGORY_ACTION_PHRASES = {
    "testing": "add a small unit test suite around one real feature and cover an edge case",
    "databases": "persist one core feature with a real schema instead of keeping everything in memory",
    "sql": "write a few real queries yourself so the data flow feels deliberate, not automatic",
    "system_design": "sketch the request flow, data model, and tradeoffs before building the next feature",
    "documentation": "write a short README that explains setup, architecture, and key decisions",
    "apis": "tighten one endpoint with validation, error handling, and clearer response shapes",
    "networking": "trace one request end to end and note headers, latency, and failure cases",
    "git": "use smaller commits and a cleaner branch flow on your next feature",
    "ci_cd": "automate linting or tests so every push gets checked",
    "docker_containers": "containerize one service so the project is easier to run consistently",
    "cloud_infra": "deploy one service and document env vars, logs, and rollback steps",
    "algorithms": "solve a couple of targeted problems and write down why your approach fits each one",
    "time_complexity": "compare runtime tradeoffs before you lock in your next solution",
    "space_complexity": "compare two solutions and note where the memory tradeoff is worth it",
    "data_structures": "implement the structure you use most often and explain when you would choose it",
    "html_css": "rebuild one UI section with cleaner spacing, layout, and semantic structure",
    "javascript_ts": "tighten your types and simplify any state flows that still feel loose",
    "react": "break one screen into smaller reusable components with clearer state boundaries",
    "responsive_design": "polish one screen on mobile and check spacing, accessibility, and hierarchy",
    "ui_ux": "refine one user flow so the next action is obvious at every step",
    "project_management": "turn the next feature into a short plan with milestones and visible scope",
    "prototyping": "ship a narrower first version sooner and validate it before adding extras",
    "integrations": "connect one outside API end to end and handle failure states cleanly",
    "problem_solving": "take one vague idea and turn it into a smaller, testable deliverable",
}


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
    """Build a concise textual summary of a user's profile for the prompt.

    Only tier labels are included – numeric scores are deliberately
    omitted so Gemini never quotes them back to the user.
    """
    lines: List[str] = []

    # Group scores by region
    groups: Dict[str, List[tuple]] = {}
    for key in CATEGORY_KEYS:
        group = CATEGORY_GROUPS[key]
        score = profile.category_scores.get(key, 0.0)
        tier = _tier_label(score)
        groups.setdefault(group, []).append(
            (CATEGORY_MAP[key], tier)
        )

    for group_name, cats in groups.items():
        avg = sum(
            profile.category_scores.get(k, 0.0)
            for k in CATEGORY_KEYS if CATEGORY_GROUPS[k] == group_name
        ) / max(len(cats), 1)
        region_tier = _tier_label(avg)
        cat_details = ", ".join(
            f"{name}: {tier}" for name, tier in cats
        )
        lines.append(
            f"  {group_name} (overall {region_tier}): {cat_details}"
        )

    top = profile.get_top_categories(5)
    top_str = ", ".join(
        f"{t['category']}: {_tier_label(t['score'])}"
        for t in top
    )

    return (
        f"Upload count: {profile.upload_count}\n"
        f"Top-5: {top_str}\n"
        f"Skills by region:\n" + "\n".join(lines)
    )


def _upload_history_summary(user_id: str) -> str:
    """Build a short summary of the user's uploaded projects/content."""
    history = get_upload_history(user_id)
    if not history:
        return "No uploads yet."

    lines: List[str] = []
    for i, snap in enumerate(history[-10:], 1):  # last 10 uploads
        source = snap.source_type.replace("_", " ").title()
        preview = snap.content_preview.strip()[:150]
        # Find top categories this upload contributed to
        top_cats = sorted(
            snap.upload_scores.items(), key=lambda kv: kv[1], reverse=True
        )[:3]
        cat_str = ", ".join(
            f"{CATEGORY_MAP.get(k, k)}: {_tier_label(v)}"
            for k, v in top_cats if v > 0.0
        )
        line = f"  {i}. [{source}] {preview}"
        if cat_str:
            line += f" — strongest in: {cat_str}"
        lines.append(line)

    return "\n".join(lines)


def _is_improvement_question(message: str) -> bool:
    """Return True when the user is explicitly asking for growth advice."""
    normalized = " ".join(message.lower().split())
    return any(keyword in normalized for keyword in _IMPROVEMENT_KEYWORDS)


def _build_chat_contents(
    message: str,
    conversation_history: Optional[List[ChatMessage]] = None,
) -> List[dict]:
    """Build the Gemini contents list and avoid duplicating the latest turn."""
    contents: List[dict] = []
    history = list(conversation_history or [])

    if history:
        last_msg = history[-1]
        if last_msg.role == "user" and last_msg.content.strip() == message.strip():
            history = history[:-1]

    for msg in history[-10:]:
        role = "user" if msg.role == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.content}]})

    contents.append({"role": "user", "parts": [{"text": message}]})
    return contents


def _build_system_prompt(profile: UserProfile, message: str) -> str:
    """Construct the system prompt that grounds the chatbot in the user's data."""
    snapshot = _profile_snapshot(profile)
    uploads = _upload_history_summary(profile.user_id)
    improvement_focus_rule = ""

    if _is_improvement_question(message):
        improvement_focus_rule = """
10. If the user asks how they can improve, what to work on, or what to
    learn next, spend at most one short sentence on strengths. Then clearly
    name 1-3 improvement areas and give a concrete next step for each.
11. Do not end the reply before directly answering the improvement part of
    the user's question.
"""

    return f"""You are Cortex, a friendly and concise CS learning advisor.

You know the user's Knowledge Map which rates their skills using these
levels: Unassessed, Novice, Beginner, Intermediate, Proficient, Advanced,
Expert.

─── CURRENT PROFILE ───
{snapshot}
────────────────────────

─── UPLOADED PROJECTS / CONTENT ───
{uploads}
────────────────────────────────────

Rules (follow strictly):
1. Keep every reply concise, usually 4-5 sentences max. Be direct and helpful.
2. NEVER mention or reveal any numeric score, percentage, or number
   between 0 and 1. Only use the level names (Novice, Beginner, etc.).
3. NEVER use XML-style tags, HTML tags, or any bracket-based markup
   in your replies. Plain text and simple markdown only.
4. Be encouraging – highlight strengths before gaps.
5. Use the level names naturally, e.g. "You're at an Intermediate level
   in Sorting" – never say "your score is 0.5".
6. For Unassessed categories, say the skill hasn't been evaluated yet,
   not that it's a weakness.
7. When the user has few uploads, suggest uploading more content.
8. If asked about something outside CS, gently redirect.
9. When relevant, reference the user's actual projects or uploads by
   name/description to make advice concrete and personal.
{improvement_focus_rule}"""


def _format_list(items: List[str]) -> str:
    """Format a short list as natural language."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _recent_upload_reference(user_id: str) -> Optional[str]:
    """Return a compact reference to the user's most recent upload."""
    history = get_upload_history(user_id)
    if not history:
        return None

    preview = " ".join(history[-1].content_preview.strip().split())
    if not preview:
        return None

    sanitized = preview.replace("`", "").replace("*", "")
    if "github.com/" in sanitized:
        repo = sanitized.rstrip("/").split("/")[-1]
        return repo[:40]

    words = sanitized.split()
    return " ".join(words[:4])[:40]


def _select_improvement_categories(profile: UserProfile, limit: int = 3) -> List[str]:
    """Pick concrete next categories that complement the user's current strengths."""
    scores = profile.category_scores
    top_categories = profile.get_top_categories(5)
    strong_keys = {
        item["category"]
        for item in top_categories
        if item["score"] >= 0.45
    }

    selected: List[str] = []
    seen_groups = set()

    ranked_weak = sorted(scores.items(), key=lambda kv: kv[1])
    for key, score in ranked_weak:
        if key in strong_keys or score == 0.0 or score >= 0.55:
            continue
        group = CATEGORY_GROUPS[key]
        if group in seen_groups:
            continue
        selected.append(key)
        seen_groups.add(group)
        if len(selected) == limit:
            return selected

    for item in top_categories:
        group = CATEGORY_GROUPS.get(item["category"])
        for candidate in _GROUP_GROWTH_RECOMMENDATIONS.get(group, ()):
            if candidate in strong_keys or candidate in selected:
                continue
            if scores.get(candidate, 0.0) >= 0.55:
                continue
            selected.append(candidate)
            if len(selected) == limit:
                return selected

    fallback_candidates = (
        "testing",
        "documentation",
        "system_design",
        "databases",
        "sql",
        "ci_cd",
    )
    for candidate in fallback_candidates:
        if candidate in strong_keys or candidate in selected:
            continue
        selected.append(candidate)
        if len(selected) == limit:
            break

    return selected


def _growth_action_phrase(category_key: str) -> str:
    """Return a concrete next-step phrase for a category."""
    phrase = _CATEGORY_ACTION_PHRASES.get(category_key)
    if phrase:
        return phrase

    label = CATEGORY_MAP.get(category_key, category_key).lower()
    group = CATEGORY_GROUPS.get(category_key, "")
    if group == "Systems":
        return f"build one backend feature that makes your {label} work visible end to end"
    if group == "Algorithms":
        return f"practice {label} with a couple of small problems and compare tradeoffs"
    if group == "Frontend":
        return f"use {label} in one polished screen that works well on desktop and mobile"
    if group == "Dev Practices":
        return f"make {label} part of your normal workflow on the next project"
    if group == "Product":
        return f"show stronger {label} by explaining your decisions before and after you build"
    return f"practice {label} in a focused feature instead of only touching it indirectly"


def _build_improvement_reply(profile: UserProfile) -> str:
    """Build a deterministic answer for 'what should I improve next?' questions."""
    strong_labels = [
        CATEGORY_MAP.get(item["category"], item["category"])
        for item in profile.get_top_categories(3)
        if item["score"] > 0.1
    ]
    improvement_keys = _select_improvement_categories(profile)
    upload_ref = _recent_upload_reference(profile.user_id)

    if strong_labels:
        if upload_ref:
            strength_sentence = (
                f"Your clearest strengths right now are {_format_list(strong_labels)}, "
                f"especially in your recent {upload_ref} work."
            )
        else:
            strength_sentence = (
                f"Your clearest strengths right now are {_format_list(strong_labels)}."
            )
    else:
        strength_sentence = (
            "I do not have enough strong evidence yet to point to clear strengths."
        )

    if not improvement_keys:
        return (
            f"{strength_sentence} The next best move is to upload one or two more repos, "
            "assignments, or code samples so I can point to sharper growth areas."
        )

    improvement_labels = [CATEGORY_MAP.get(key, key) for key in improvement_keys]
    action_phrases = [_growth_action_phrase(key) for key in improvement_keys]

    reply = (
        f"{strength_sentence} The clearest next areas to improve are "
        f"{_format_list(improvement_labels)}. Next, {_format_list(action_phrases)}."
    )

    if profile.upload_count < 3:
        reply += (
            " One more upload that shows testing, data handling, or architecture "
            "would make this advice even sharper."
        )

    return reply


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
    profile = get_user_profile(user_id)
    if profile is None:
        return ChatResponse(
            reply="I don't have a profile for you yet. Please upload some content first so I can learn about your skills!",
            suggestions=[
                "How do I upload a GitHub repo?",
                "What kind of content can I upload?",
            ],
        )

    if _is_improvement_question(message):
        return ChatResponse(
            reply=_build_improvement_reply(profile),
            suggestions=_generate_suggestions(profile, message),
        )

    from google import genai

    system_prompt = _build_system_prompt(profile, message)
    contents = _build_chat_contents(message, conversation_history)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model, 
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7,
                "max_output_tokens": 800,
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
