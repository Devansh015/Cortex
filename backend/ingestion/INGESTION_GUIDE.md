# Ingestion Pipeline Documentation

## Overview

The ingestion pipeline is a production-ready Python system that accepts flexible user input, automatically detects the input type, processes it appropriately, chunks the content for semantic retrieval, and stores everything in Backboard.io.

## Supported Input Types

### 1. Plain Text Prompts
User-provided text describing:
- Skills and expertise
- Interests and passions
- Experiences and accomplishments
- Project ideas and thoughts
- Preferences and opinions
- General knowledge

The system automatically infers the category of the text.

**Example:**
```python
input_data = "I'm skilled in Python and JavaScript. Built several web applications."
```

### 2. GitHub Repository URLs
Links to GitHub repositories:
- Extracts repository metadata
- Fetches README content
- Identifies programming languages
- Stores relevant project information

**Example:**
```python
input_data = "https://github.com/openai/gpt-3"
```

### 3. PDF Documents
PDF files for document management:
- Extracts text from all pages
- Preserves document structure
- Handles multi-page documents
- Includes document metadata

**Example:**
```python
input_data = "/path/to/research_paper.pdf"
```

## Quick Start

### Basic Usage

```python
from backend.ingestion import ingest_input

# Ingest any type of input
result = ingest_input(
    user_id="user_123",
    input_data="I'm interested in machine learning and AI"
)

print(result)
# {
#     "detected_input_type": "text_prompt",
#     "status": "success",
#     "chunks_created": 3,
#     "items_stored": 3,
#     "metadata_summary": {...}
# }
```

### With File Upload

```python
from pathlib import Path

result = ingest_input(
    user_id="user_123",
    input_data="/uploads/document.pdf",
    file_name="Research Paper.pdf"
)
```

### Using Pipeline Directly

```python
from backend.ingestion import IngestionPipeline

# Create pipeline with custom settings
pipeline = IngestionPipeline(
    chunking_strategy="semantic",
    enable_logging=True
)

# Ingest data
result = pipeline.ingest(
    user_id="user_123",
    input_data="Your input here"
)
```

## Architecture

### Component Modules

1. **input_detector.py**
   - Detects input type automatically
   - Validates input format
   - Extracts type-specific metadata

2. **text_processor.py**
   - Cleans and normalizes text
   - Infers content category
   - Extracts key terms
   - Generates summaries

3. **github_processor.py**
   - Fetches repo metadata via GitHub API
   - Extracts README content
   - Identifies programming languages
   - Compiles comprehensive repo description

4. **pdf_processor.py**
   - Extracts text from PDF files
   - Handles multi-page documents
   - Preserves document metadata
   - Validates PDF integrity

5. **chunker.py**
   - Splits content into semantic chunks
   - Implements overlap for context preservation
   - Supports multiple chunking strategies
   - Attaches metadata to each chunk

6. **backboard_client.py**
   - Abstracts Backboard.io API
   - Provides LocalMemoryStore for development
   - Separates storage by input type
   - Handles user-aware storage

7. **ingestion_pipeline.py**
   - Orchestrates entire pipeline
   - Routes inputs to appropriate processors
   - Manages error handling
   - Returns structured results

### Data Flow

```
User Input
    ↓
Detect Type → Validate
    ↓
Route by Type
    ├─ Text → TextProcessor
    ├─ GitHub → GitHubProcessor
    └─ PDF → PDFProcessor
    ↓
Process & Extract Content
    ↓
Generate Metadata
    ↓
Chunk Content
    ├─ Semantic Chunker (default)
    └─ Fixed-Size Chunker (alternative)
    ↓
Store in Backboard
    ├─ text_prompts collection
    ├─ github_repositories collection
    └─ documents collection
    ↓
Return Result
```

## Configuration

### Environment Variables

```bash
# Backboard.io
export BACKBOARD_API_KEY="your_api_key"
export BACKBOARD_API_URL="https://api.backboard.io"

# GitHub (optional, increases rate limits)
export GITHUB_TOKEN="your_github_token"
```

### Pipeline Configuration

```python
pipeline = IngestionPipeline(
    memory_adapter=custom_adapter,  # Optional
    chunking_strategy="semantic",   # or "fixed"
    enable_logging=True
)
```

## Response Format

All ingestion calls return a structured response:

```python
{
    "detected_input_type": "text_prompt",  # or github_repo, pdf
    "status": "success",                    # or "error"
    "chunks_created": 5,
    "items_stored": 5,
    "metadata_summary": {
        "source_type": "text_prompt",
        "category": "skill",
        "content_length": 245,
        "word_count": 42,
        "timestamp": "2024-03-07T10:30:00"
    },
    "details": {
        "processing": {...},
        "chunking": {...},
        "storage": {...}
    }
}
```

## Text Category Inference

For text prompts, the system infers categories:

- **skill**: "I know Python", "Experienced with", "Proficient in"
- **interest**: "Interested in", "Passionate about", "Love", "Curious"
- **experience**: "Built", "Worked on", "Implemented", "Led"
- **project_idea**: "Planning to", "Want to", "Thinking about"
- **preference**: "Prefer", "Like", "Favorite", "Dislike"
- **knowledge**: Default for general statements

The confidence score indicates how strongly the text matches a category.

## Chunking Strategies

### Semantic Chunking (Default)

Chunks content at semantic boundaries (sentences and paragraphs) while maintaining overlap for context:

```python
chunker = SemanticChunker(
    target_size=512,      # Target characters per chunk
    overlap=128,          # Overlap between chunks
    min_chunk_size=100    # Minimum chunk size
)
```

**Best for:** Documents, research papers, long-form content

### Fixed-Size Chunking

Divides content into fixed-size chunks with consistent overlap:

```python
chunker = FixedSizeChunker(
    chunk_size=512,
    overlap=128
)
```

**Best for:** Consistent structure, streaming data

## Error Handling

The pipeline includes comprehensive error handling:

```python
result = ingest_input("user_123", "invalid pdf")

if result["status"] == "error":
    print(f"Error: {result.get('error')}")
    # Handle error appropriately
```

Common error cases:
- Invalid GitHub URL
- Missing PDF file
- Empty text input
- API failures
- Network timeouts
- Malformed content

## Integration with FastAPI

Example FastAPI endpoint:

```python
from fastapi import FastAPI, UploadFile, File
from backend.ingestion import IngestionPipeline

app = FastAPI()
pipeline = IngestionPipeline()

@app.post("/api/ingest")
async def ingest(user_id: str, input_data: str):
    result = pipeline.ingest(user_id, input_data)
    return result

@app.post("/api/ingest/pdf")
async def ingest_pdf(user_id: str, file: UploadFile = File(...)):
    content = await file.read()
    result = pipeline.ingest(user_id, content, file.filename)
    return result
```

## Backboard.io Storage Structure

Chunks are stored with the following structure:

```python
{
    "id": "chunk_id",
    "content": "chunk text...",
    "metadata": {
        "user_id": "user_123",
        "source_type": "text_prompt",           # or github_repo, pdf
        "category": "skill",
        "chunk_index": 0,
        "chunk_count": 5,
        "ingestion_timestamp": "2024-03-07T...",
        "source_start": 0,
        "source_end": 512,
        
        # Text-specific
        "inferred_category": "skill",
        "key_terms": ["python", "machine learning"],
        
        # GitHub-specific
        "repo_url": "https://github.com/...",
        "repo_name": "gpt-3",
        "owner": "openai",
        "languages": ["Python", "JavaScript"],
        
        # PDF-specific
        "file_name": "document.pdf",
        "page_count": 50
    }
}
```

Collections in Backboard:
- `text_prompts`: Text-based user input
- `github_repositories`: GitHub repo data
- `documents`: PDF and document content

## Performance Considerations

### Chunking
- Semantic chunking is slower but preserves meaning
- Fixed-size chunking is faster for large volumes
- Overlap increases storage but improves retrieval quality

### API Calls
- GitHub API has rate limits (authenticated: 5000/hour)
- Backboard API calls are batched for efficiency
- Consider caching for repeated inputs

### Memory
- Large PDFs (>50MB) are rejected to prevent memory issues
- Consider pagination for very large result sets
- Streaming for very large document processing

## Examples

### Example 1: Ingest User Skill

```python
from backend.ingestion import ingest_input

result = ingest_input(
    user_id="alice_001",
    input_data="I have 5 years of experience with React and Node.js. "
               "Built several production web applications."
)

print(f"Stored {result['items_stored']} chunks")
print(f"Category: {result['metadata_summary']['category']}")
```

### Example 2: Ingest GitHub Repository

```python
result = ingest_input(
    user_id="bob_001",
    input_data="https://github.com/facebook/react"
)

print(f"Repo: {result['details']['storage']['chunk_ids']}")
```

### Example 3: Ingest PDF Document

```python
result = ingest_input(
    user_id="charlie_001",
    input_data="/documents/research_paper.pdf"
)

if result['status'] == 'success':
    print(f"Chunked into {result['chunks_created']} pieces")
    print(f"Stored in Backboard: {result['items_stored']} items")
```

### Example 4: Search User Memories

```python
from backend.ingestion import BackboardMemoryAdapter

adapter = BackboardMemoryAdapter()

# Search across all types
results = adapter.search_memories(
    user_id="user_123",
    query="machine learning",
    limit=10
)

# Search only GitHub repos
results = adapter.search_memories(
    user_id="user_123",
    query="python projects",
    source_type="github_repo",
    limit=5
)
```

## Testing

The module includes local storage for testing:

```python
from backend.ingestion import IngestionPipeline, LocalMemoryStore

# Use local store instead of Backboard API
local_store = LocalMemoryStore()
adapter = BackboardMemoryAdapter(local_store)
pipeline = IngestionPipeline(memory_adapter=adapter)

# Test without API keys
result = pipeline.ingest("test_user", "test input")
```

## Troubleshooting

### GitHub API Rate Limit
Set `GITHUB_TOKEN` environment variable to increase rate limit from 60 to 5000 requests/hour.

### PDF Extraction Issues
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Check that PDF is not encrypted or corrupted
- Large PDFs (>50MB) are automatically rejected

### Backboard Connection Error
- Verify `BACKBOARD_API_KEY` is set correctly
- Check `BACKBOARD_API_URL` endpoint
- Ensure network connectivity

### Empty Content Extraction
- Text input might be too short or contain only whitespace
- PDF might not have extractable text (scanned image)
- GitHub repo might be empty or inaccessible

## Future Enhancements

- [ ] Support for more file types (DOCX, EPUB, etc.)
- [ ] Web scraping for URL inputs
- [ ] Image-based OCR for scanned PDFs
- [ ] Integration with more APIs (Notion, Google Drive, etc.)
- [ ] Incremental ingestion with change detection
- [ ] Distributed processing for large files
- [ ] Advanced deduplication across ingestions
- [ ] Multi-language support

## License

This ingestion pipeline is part of the Knowledge Map project.
