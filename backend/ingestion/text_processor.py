"""
Text prompt processor module.
Handles user-provided text input (skills, interests, experiences, ideas, etc.)
"""

import re
from typing import Dict, Any, List
from datetime import datetime
from .input_detector import _infer_text_category


class TextPromptProcessor:
    """Process and normalize plain text user input."""
    
    def __init__(self):
        self.min_text_length = 5  # Minimum characters for valid text
    
    def process(
        self,
        text: str,
        user_id: str,
        inferred_category: str = None,
    ) -> Dict[str, Any]:
        """
        Process a text prompt from the user.
        
        Args:
            text: The plain text input
            user_id: The user ID for tracking
            inferred_category: Pre-inferred category if available
        
        Returns:
            Dict with:
            - content: Cleaned and normalized text
            - category: Inferred category (skill, interest, experience, etc.)
            - summary: Brief summary of the content
            - metadata: Additional metadata
            - validation: Validation results
        """
        
        # Validate input
        validation = self._validate_text(text)
        if not validation["is_valid"]:
            error_msg = validation.get("error") or "; ".join(validation.get("errors", ["Validation failed"]))
            return {
                "content": text,
                "category": "unknown",
                "summary": "",
                "metadata": {"error": error_msg},
                "validation": validation,
            }
        
        # Clean and normalize
        cleaned_text = self._normalize_text(text)
        
        # Infer category if not provided
        if not inferred_category:
            detection = _infer_text_category(cleaned_text)
            category = detection["inferred_category"]
        else:
            category = inferred_category
        
        # Extract key entities/terms
        key_terms = self._extract_key_terms(cleaned_text)
        
        # Generate summary
        summary = self._generate_summary(cleaned_text)
        
        # Build metadata
        metadata = {
            "source_type": "text_prompt",
            "category": category,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "content_length": len(cleaned_text),
            "word_count": len(cleaned_text.split()),
            "key_terms": key_terms,
            "language": "en",  # Could be extended to detect language
        }
        
        return {
            "content": cleaned_text,
            "category": category,
            "summary": summary,
            "metadata": metadata,
            "validation": validation,
        }
    
    def _validate_text(self, text: str) -> Dict[str, Any]:
        """Validate that text meets minimum requirements."""
        errors = []
        
        if not isinstance(text, str):
            errors.append("Input must be a string")
        elif len(text.strip()) == 0:
            errors.append("Text cannot be empty")
        elif len(text.strip()) < self.min_text_length:
            errors.append(f"Text must be at least {self.min_text_length} characters")
        
        # Check for obvious spam or gibberish
        if self._is_likely_spam(text):
            errors.append("Text appears to be spam or gibberish")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "text_length": len(text),
            "stripped_length": len(text.strip()),
        }
    
    def _normalize_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Strip whitespace
        text = text.strip()
        
        # Normalize line breaks (replace multiple with single)
        text = re.sub(r"\n\n+", "\n", text)
        
        # Remove extra spaces
        text = re.sub(r" {2,}", " ", text)
        
        # Remove trailing punctuation and spaces
        text = text.rstrip()
        
        return text
    
    def _is_likely_spam(self, text: str) -> bool:
        """Detect obvious spam or gibberish."""
        # Check for too many special characters
        special_count = sum(1 for c in text if not c.isalnum() and c not in " \n.,!?'-")
        if len(text) > 0 and special_count / len(text) > 0.5:
            return True
        
        # Check for repeated characters
        if re.search(r"(.)\1{10,}", text):
            return True
        
        return False
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract important terms and keywords from text."""
        # Split into words and filter
        words = text.lower().split()
        
        # Remove common stopwords
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "be", "have", "has",
            "do", "does", "did", "will", "would", "could", "should", "may", "might",
            "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
        }
        
        key_terms = []
        for word in words:
            # Clean word of punctuation
            clean_word = re.sub(r"[^\w\-]", "", word)
            # Keep if not stopword and at least 3 chars
            if clean_word and len(clean_word) >= 3 and clean_word not in stopwords:
                if clean_word not in key_terms:  # Avoid duplicates
                    key_terms.append(clean_word)
        
        return key_terms[:15]  # Return top 15 key terms
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a summary by taking the first sentences."""
        # Split into sentences
        sentences = re.split(r"[.!?]+", text)
        
        summary = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                if len(summary) + len(sentence) + 1 <= max_length:
                    if summary:
                        summary += " " + sentence
                    else:
                        summary = sentence
                else:
                    break
        
        return summary.rstrip() + ("." if summary and not summary.endswith((".","!", "?")) else "")


# Example usage
if __name__ == "__main__":
    processor = TextPromptProcessor()
    
    # Test cases
    test_prompts = [
        "I'm skilled in Python, JavaScript, and React. I have 5 years of web development experience.",
        "Interested in machine learning and AI applications in healthcare",
        "I built a real-time chat application using Node.js and WebSockets",
    ]
    
    for prompt in test_prompts:
        result = processor.process(prompt, user_id="user_123")
        print(f"Original: {prompt}")
        print(f"Category: {result['category']}")
        print(f"Summary: {result['summary']}")
        print(f"Key terms: {result['metadata']['key_terms']}\n")
