"""
Input type detection module for the ingestion pipeline.
Determines whether input is plain text, GitHub URL, PDF, or other types.
"""

import re
from typing import Literal, Dict, Any
from pathlib import Path
import os

InputType = Literal["text_prompt", "github_repo", "pdf", "url", "file", "unknown"]


def detect_input_type(input_data: Any) -> Dict[str, Any]:
    """
    Detect the type of input and return relevant metadata.
    
    Args:
        input_data: The user input (string, bytes, or file path)
    
    Returns:
        Dict with:
        - detected_type: InputType
        - is_valid: bool
        - metadata: dict with type-specific info
        - raw_value: The original input
    """
    
    # Handle bytes (from file upload)
    if isinstance(input_data, bytes):
        return _detect_file_type_from_bytes(input_data)
    
    # Handle file path (Path object or string path)
    if isinstance(input_data, Path) or (isinstance(input_data, str) and os.path.exists(input_data)):
        return _detect_file_type_from_path(input_data)
    
    # Handle string input
    if isinstance(input_data, str):
        input_str = input_data.strip()
        
        # Check if it looks like a file path (even if file doesn't exist)
        if input_str.lower().endswith(".pdf"):
            return {
                "detected_type": "pdf",
                "is_valid": os.path.exists(input_str),
                "metadata": {
                    "file_name": os.path.basename(input_str),
                    "file_path": input_str,
                    "error": None if os.path.exists(input_str) else f"File does not exist: {input_str}",
                },
                "raw_value": input_str,
            }
        
        # Check for GitHub URL
        if _is_github_url(input_str):
            return {
                "detected_type": "github_repo",
                "is_valid": True,
                "metadata": _extract_github_metadata(input_str),
                "raw_value": input_str,
            }
        
        # Check for generic URL
        if _is_url(input_str):
            return {
                "detected_type": "url",
                "is_valid": True,
                "metadata": {"url": input_str},
                "raw_value": input_str,
            }
        
        # Default to text prompt
        return {
            "detected_type": "text_prompt",
            "is_valid": True,
            "metadata": _infer_text_category(input_str),
            "raw_value": input_str,
        }
    
    # Unknown type
    return {
        "detected_type": "unknown",
        "is_valid": False,
        "metadata": {"error": "Unsupported input type"},
        "raw_value": input_data,
    }


def _is_github_url(text: str) -> bool:
    """Check if text is a valid GitHub repository URL."""
    github_pattern = r"^(https?://)?(www\.)?github\.com/[\w\-\.]+/[\w\-\.]+(/?)$"
    return bool(re.match(github_pattern, text.strip()))


def _is_url(text: str) -> bool:
    """Check if text is a valid URL."""
    url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(url_pattern, text.strip(), re.IGNORECASE))


def _extract_github_metadata(url: str) -> Dict[str, str]:
    """Extract repository owner and name from GitHub URL."""
    # Normalize the URL
    url = url.strip().rstrip("/")
    
    # Extract owner and repo name
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if match:
        owner, repo = match.groups()
        return {
            "url": url if url.startswith("http") else f"https://{url}",
            "owner": owner,
            "repo_name": repo,
            "full_repo_path": f"{owner}/{repo}",
        }
    
    return {"url": url, "error": "Could not parse GitHub URL"}


def _infer_text_category(text: str) -> Dict[str, Any]:
    """
    Infer the category of a text prompt.
    Categories: skill, interest, experience, project_idea, preference, knowledge
    """
    text_lower = text.lower()
    
    # Define keywords for each category
    skill_keywords = ["know", "skilled in", "experienced with", "proficient", "can", "able to", "expertise"]
    interest_keywords = ["interested in", "passionate about", "love", "enjoy", "fascinated by", "curious about"]
    experience_keywords = ["worked on", "built", "developed", "created", "implemented", "led", "managed", "project"]
    project_keywords = ["building", "creating", "developing", "idea for", "want to", "planning to", "thinking about"]
    preference_keywords = ["prefer", "like", "don't like", "favorite", "hate", "avoid", "dislike"]
    
    # Count keyword matches
    categories_score = {
        "skill": sum(1 for kw in skill_keywords if kw in text_lower),
        "interest": sum(1 for kw in interest_keywords if kw in text_lower),
        "experience": sum(1 for kw in experience_keywords if kw in text_lower),
        "project_idea": sum(1 for kw in project_keywords if kw in text_lower),
        "preference": sum(1 for kw in preference_keywords if kw in text_lower),
    }
    
    # Determine the most likely category
    inferred_category = max(categories_score, key=categories_score.get) if max(categories_score.values()) > 0 else "knowledge"
    
    return {
        "inferred_category": inferred_category,
        "category_confidence": max(categories_score.values()),
        "text_length": len(text),
        "word_count": len(text.split()),
    }


def _detect_file_type_from_path(file_path: Any) -> Dict[str, Any]:
    """Detect file type from file path."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            "detected_type": "unknown",
            "is_valid": False,
            "metadata": {"error": "File does not exist"},
            "raw_value": str(file_path),
        }
    
    suffix = file_path.suffix.lower()
    
    if suffix == ".pdf":
        return {
            "detected_type": "pdf",
            "is_valid": True,
            "metadata": {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
            },
            "raw_value": str(file_path),
        }
    
    if suffix in [".txt", ".md", ".doc", ".docx"]:
        return {
            "detected_type": "file",
            "is_valid": True,
            "metadata": {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": suffix,
                "file_size": file_path.stat().st_size,
            },
            "raw_value": str(file_path),
        }
    
    return {
        "detected_type": "unknown",
        "is_valid": False,
        "metadata": {"error": f"Unsupported file type: {suffix}"},
        "raw_value": str(file_path),
    }


def _detect_file_type_from_bytes(data: bytes) -> Dict[str, Any]:
    """Detect file type from file bytes (magic numbers)."""
    # PDF magic number: %PDF
    if data.startswith(b"%PDF"):
        return {
            "detected_type": "pdf",
            "is_valid": True,
            "metadata": {"file_size": len(data)},
            "raw_value": data[:100],  # Return first 100 bytes as sample
        }
    
    # Try to decode as text
    try:
        text = data.decode("utf-8")
        return {
            "detected_type": "file",
            "is_valid": True,
            "metadata": {"file_size": len(data), "encoding": "utf-8"},
            "raw_value": data[:100],
        }
    except UnicodeDecodeError:
        pass
    
    return {
        "detected_type": "unknown",
        "is_valid": False,
        "metadata": {"error": "Could not determine file type from bytes"},
        "raw_value": data[:100],
    }


# Test helpers
if __name__ == "__main__":
    # Test cases
    test_inputs = [
        "https://github.com/openai/gpt-3",
        "I'm skilled in Python and JavaScript",
        "Interested in machine learning and AI",
        "https://example.com",
        "I built a web scraper last year",
    ]
    
    for test_input in test_inputs:
        result = detect_input_type(test_input)
        print(f"Input: {test_input[:50]}...")
        print(f"Detected: {result['detected_type']}")
        print(f"Metadata: {result['metadata']}\n")