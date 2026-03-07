"""
Ingestion Pipeline Module
========================

A production-ready Python ingestion pipeline for processing diverse user inputs
and storing them in Backboard.io for semantic retrieval and memory management.

Supports:
- Plain text prompts (skills, interests, experiences, ideas)
- GitHub repository links
- PDF documents
- Flexible architecture for future input types

Main entry point:
    from backend.ingestion import ingest_input
    
    result = ingest_input(
        user_id="user_123",
        input_data="Your text or URL or file path"
    )
"""

from .ingestion_pipeline import IngestionPipeline, ingest_input
from .input_detector import detect_input_type
from .text_processor import TextPromptProcessor
from .github_processor import GitHubProcessor
from .pdf_processor import PDFProcessor
from .chunker import SemanticChunker, FixedSizeChunker, create_chunker
from .backboard_client import (
    BackboardClient,
    BackboardAPIClient,
    BackboardMemoryAdapter,
    LocalMemoryStore,
)

__all__ = [
    "IngestionPipeline",
    "ingest_input",
    "detect_input_type",
    "TextPromptProcessor",
    "GitHubProcessor",
    "PDFProcessor",
    "SemanticChunker",
    "FixedSizeChunker",
    "create_chunker",
    "BackboardClient",
    "BackboardAPIClient",
    "BackboardMemoryAdapter",
    "LocalMemoryStore",
]
