"""
Regression tests for chatbot prompt and request shaping.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from chatbot.chat_service import (  # noqa: E402
    _build_chat_contents,
    _build_improvement_reply,
    _build_system_prompt,
    chat_with_profile,
)
from chatbot.models import ChatMessage  # noqa: E402
from profile_scoring.models import UserProfile  # noqa: E402


def _make_profile() -> UserProfile:
    profile = UserProfile(user_id="chat_test_user")
    profile.upload_count = 2
    profile.category_scores["apis"] = 0.62
    profile.category_scores["variables"] = 0.58
    profile.category_scores["functions"] = 0.56
    profile.category_scores["testing"] = 0.24
    return profile


class ChatServiceTests(unittest.TestCase):
    def test_build_chat_contents_deduplicates_latest_user_message(self):
        contents = _build_chat_contents(
            "Where can I improve?",
            conversation_history=[
                ChatMessage(role="assistant", content="You have a solid backend base."),
                ChatMessage(role="user", content="Where can I improve?"),
            ],
        )

        self.assertEqual([item["role"] for item in contents], ["model", "user"])
        self.assertEqual(contents[-1]["parts"][0]["text"], "Where can I improve?")

    def test_build_system_prompt_adds_growth_rule_for_improvement_questions(self):
        prompt = _build_system_prompt(_make_profile(), "What should I improve next?")

        self.assertIn("spend at most one short sentence on strengths", prompt)
        self.assertIn("Do not end the reply before directly answering", prompt)

    def test_build_system_prompt_keeps_general_prompt_for_other_questions(self):
        prompt = _build_system_prompt(_make_profile(), "What projects fit my strengths?")

        self.assertNotIn("spend at most one short sentence on strengths", prompt)

    @patch("chatbot.chat_service.get_upload_history")
    def test_build_improvement_reply_names_growth_areas_and_steps(self, mock_history):
        mock_history.return_value = []

        reply = _build_improvement_reply(_make_profile())

        self.assertIn("The clearest next areas to improve are", reply)
        self.assertIn("Testing", reply)
        self.assertIn("Next,", reply)

    @patch("chatbot.chat_service.get_user_profile")
    @patch("chatbot.chat_service._generate_suggestions")
    @patch("chatbot.chat_service._build_improvement_reply")
    def test_chat_with_profile_bypasses_model_for_improvement_questions(
        self,
        mock_build_reply,
        mock_suggestions,
        mock_get_profile,
    ):
        mock_get_profile.return_value = _make_profile()
        mock_build_reply.return_value = "Deterministic growth advice"
        mock_suggestions.return_value = ["How can I improve my Testing skills?"]

        response = chat_with_profile("chat_test_user", "What can I improve next?")

        self.assertEqual(response.reply, "Deterministic growth advice")
        self.assertEqual(response.suggestions, ["How can I improve my Testing skills?"])
        mock_build_reply.assert_called_once()


if __name__ == "__main__":
    unittest.main()
