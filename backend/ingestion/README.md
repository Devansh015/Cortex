# Backend Ingestion Pipeline

A production-ready Python ingestion pipeline that intelligently processes diverse user inputs and stores them in Backboard.io for semantic retrieval and memory management.

## Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Basic Usage

```python
from backend.ingestion import ingest_input

# Process any type of input
result = ingest_input(
    user_id="user_123",
    input_data="I'm skilled in Python and machine learning"
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

## Supported Input Types

### 1. Text Prompts
User-provided statements about:
- Skills and expertise
- Interests and passions  
- Experiences and accomplishments
- Project ideas
- Preferences and opinions

**Example:**
```python
ingest_input("user_1", "I'm skilled in Python and JavaScript")
```

### 2. GitHub Repositories
Links to GitHub repositories:

**Example:**
```python
ingest_input("user_1", "https://github.com/openai/gpt-3")
```

### 3. PDF Documents
PDF files with text content:

**Example:**
```python
ingest_input("user_1", "/path/to/document.pdf")
```

## Core Features

✅ **Automatic Input Detection** - Identifies input type instantly
✅ **Type-Specific Processing** - Each input type has optimized processing
✅ **Smart Chunking** - Semantic or fixed-size chunking strategies
✅ **Category Inference** - Automatically categorizes text input
✅ **Metadata Enrichment** - Extracts and preserves useful metadata
✅ **Error Handling** - Comprehensive validation and error messages
✅ **Backboard Integration** - Stores results in organized collections
✅ **Local Testing** - In-memory storage for development

## Architecture

### Module Structure

```
backend/ingestion/
├── __init__.py                 # Package exports
├── config.py                   # Configuration settings
├── input_detector.py           # Input type detection
├── text_processor.py           # Text processing and categorization
├── github_processor.py         # GitHub API integration
├── pdf_processor.py            # PDF text extraction
├── chunker.py                  # Content chunking strategies
├── backboard_client.py         # Backboard.io storage adapter
├── ingestion_pipeline.py       # Main orchestration
├── examples.py                 # Comprehensive examples
├── INGESTION_GUIDE.md          # Detailed documentation
└── tests.py                    # Unit tests
```

### Data Processing Flow

```
User Input
    ↓
Input Detection
    ├─ Text Prompt → TextProcessor
    ├─ GitHub URL → GitHubProcessor  
    └─ PDF File → PDFProcessor
    ↓
Content Extraction & Processing
    ↓
Metadata Generation
    ↓
Content Chunking
    (Semantic or Fixed-Size)
    ↓
Backboard Storage
    (Organized by type and user)
    ↓
Structured Response
```

## Configuration

### Environment Variables

```bash
# Backboard.io (required for production)
export BACKBOARD_API_KEY="your_api_key"
export BACKBOARD_API_URL="https://api.backboard.io"

# GitHub (optional, increases rate limits)
export GITHUB_TOKEN="your_github_token"

# Logging
export LOG_LEVEL="INFO"
export ENABLE_LOGGING="True"
```

### Programmatic Configuration

```python
from backend.ingestion import IngestionConfig

# Check configuration
config = IngestionConfig()
config.validate()  # Returns validation results
```

## API Reference

### Main Functions

#### `ingest_input(user_id, input_data, file_name=None)`

Simple function for ingesting data.

```python
result = ingest_input(
    user_id="user_123",
    input_data="Your input here",
    file_name="optional_filename.pdf"  # For PDFs
)
```

**Returns:**
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
        "timestamp": "2024-03-07T..."
    },
    "details": {...}
}
```

### Pipeline Class

```python
from backend.ingestion import IngestionPipeline

pipeline = IngestionPipeline(
    memory_adapter=None,           # Custom adapter (optional)
    chunking_strategy="semantic",  # or "fixed"
    enable_logging=True            # Enable pipeline logging
)

result = pipeline.ingest(user_id, input_data, file_name)
```

### Processors

#### TextPromptProcessor

```python
from backend.ingestion import TextPromptProcessor

processor = TextPromptProcessor()
result = processor.process(text, user_id)
```

#### GitHubProcessor

```python
from backend.ingestion import GitHubProcessor

processor = GitHubProcessor(github_token="optional_token")
result = processor.process(repo_url, user_id)
```

#### PDFProcessor

```python
from backend.ingestion import PDFProcessor

processor = PDFProcessor()
result = processor.process(pdf_path, user_id, file_name="optional")
```

### Chunking

```python
from backend.ingestion import SemanticChunker, FixedSizeChunker

# Semantic chunking (preserves meaning)
chunker = SemanticChunker(
    target_size=512,
    overlap=128,
    min_chunk_size=100
)

# Fixed-size chunking (consistent size)
chunker = FixedSizeChunker(
    chunk_size=512,
    overlap=128
)

chunks = chunker.chunk(content, metadata)
```

### Storage

```python
from backend.ingestion import BackboardMemoryAdapter

adapter = BackboardMemoryAdapter()

# Store
result = adapter.save_ingestion_result(
    user_id="user_123",
    input_type="text_prompt",
    chunks=[...],
    metadata={...}
)

# Search
memories = adapter.search_memories(
    user_id="user_123",
    query="machine learning",
    source_type="text_prompt",  # optional
    limit=10
)
```

## Examples

### Example 1: Skill Ingestion

```python
from backend.ingestion import ingest_input

result = ingest_input(
    user_id="alice_001",
    input_data="I have 5 years of React experience and built several production apps"
)

# Result will automatically categorize as "skill"
print(f"Category: {result['metadata_summary']['category']}")  # "skill"
```

### Example 2: GitHub Repository

```python
result = ingest_input(
    user_id="bob_001",
    input_data="https://github.com/vercel/next.js"
)

# Extracts repo info, languages, README, etc.
print(f"Languages: {result['details']['storage']['languages']}")
```

### Example 3: PDF Document

```python
result = ingest_input(
    user_id="charlie_001",
    input_data="/documents/research_paper.pdf"
)

# Extracts text, chunks, and stores with metadata
print(f"Pages extracted: {result['details']['processing']['metadata']['page_count']}")
```

### Example 4: Memory Search

```python
from backend.ingestion import BackboardMemoryAdapter

adapter = BackboardMemoryAdapter()

# Search across all types
results = adapter.search_memories("user_123", "python")

# Search only repositories
results = adapter.search_memories(
    "user_123", 
    "web framework",
    source_type="github_repo"
)
```

## FastAPI Integration

```python
from fastapi import FastAPI, UploadFile, File
from backend.ingestion import IngestionPipeline

app = FastAPI()
pipeline = IngestionPipeline()

@app.post("/api/ingest/text")
async def ingest_text(user_id: str, text: str):
    result = pipeline.ingest(user_id, text)
    return result

@app.post("/api/ingest/pdf")
async def ingest_pdf(user_id: str, file: UploadFile = File(...)):
    content = await file.read()
    result = pipeline.ingest(user_id, content, file.filename)
    return result

@app.post("/api/ingest/github")
async def ingest_repo(user_id: str, repo_url: str):
    result = pipeline.ingest(user_id, repo_url)
    return result
```

## Text Categories

The pipeline automatically infers the category of text inputs:

| Category | Keywords | Example |
|----------|----------|---------|
| **skill** | know, proficient, expertise | "I'm skilled in Python" |
| **interest** | interested, passionate, love | "Passionate about ML" |
| **experience** | built, worked, implemented | "Built a web app" |
| **project_idea** | planning, thinking, want to | "Planning to build an AI system" |
| **preference** | prefer, like, favorite | "Prefer TypeScript over JS" |
| **knowledge** | (default) | Any other statement |

## Backboard Storage Structure

Chunks are stored with comprehensive metadata:

```python
{
    "id": "chunk_123",
    "content": "Extracted content...",
    "metadata": {
        "user_id": "user_123",
        "source_type": "text_prompt",  # text_prompt, github_repo, or pdf
        "category": "skill",
        "chunk_index": 0,
        "chunk_count": 5,
        "ingestion_timestamp": "2024-03-07T...",
        "source_start": 0,
        "source_end": 512,
        "key_terms": ["python", "machine learning"],  # Text-specific
        "repo_url": "https://...",                   # GitHub-specific
        "file_name": "document.pdf"                  # PDF-specific
    }
}
```

## Error Handling

The pipeline validates all inputs and provides detailed error messages:

```python
result = ingest_input("user_123", "invalid content")

if result["status"] == "error":
    print(f"Error: {result.get('error')}")
    # Handle appropriately
```

Common error cases:
- Empty or whitespace-only text
- Invalid GitHub URL format
- Missing or corrupted PDF file
- Network/API failures
- Invalid user input

## Testing

Run the comprehensive examples:

```bash
python -m backend.ingestion.examples
```

Examples include:
1. Basic text prompt ingestion
2. Category inference
3. GitHub processing
4. PDF processing
5. Chunking strategies
6. Backboard storage
7. Full pipeline integration
8. Error handling
9. FastAPI integration

## Performance Notes

- **Text Processing**: ~1-5ms per input
- **GitHub Processing**: ~500ms-2s (API dependent)
- **PDF Processing**: ~100ms-2s (size dependent)
- **Chunking**: ~10-50ms (content dependent)
- **Storage**: ~100-500ms (batch size dependent)

### Optimization Tips

- Use semantic chunking for better retrieval quality
- Cache GitHub API results when possible
- Batch multiple ingestions
- Use connection pooling for API calls
- Consider incremental processing for large files

## Troubleshooting

### GitHub API Rate Limit
Set `GITHUB_TOKEN` to increase limit from 60 to 5000 requests/hour.

### PDF Extraction Issues
- Ensure PyPDF2 is installed
- Check PDF is not encrypted
- Large PDFs (>50MB) are rejected

### Backboard Connection Error
- Verify `BACKBOARD_API_KEY` is set
- Check `BACKBOARD_API_URL` is accessible
- Ensure network connectivity

### Empty Content Extraction
- Text might be too short
- PDF might be scanned image (no OCR)
- GitHub repo might be inaccessible

## Future Enhancements

- [ ] DOCX, EPUB support
- [ ] Web scraping
- [ ] Image OCR for PDFs
- [ ] Notion, Google Drive integration
- [ ] Incremental updates
- [ ] Distributed processing
- [ ] Deduplication
- [ ] Multi-language support

## Contributing

The pipeline is designed to be extended:

1. **Add Input Type**: Create processor in `{type}_processor.py`
2. **Add Chunking Strategy**: Extend `ChunkingStrategy` base class
3. **Add Storage Backend**: Implement `BackboardClient` interface

## License

Part of the Knowledge Map project.

## Support

For issues or questions:
- Check `INGESTION_GUIDE.md` for detailed documentation
- Review `examples.py` for usage patterns
- Check logs with `enable_logging=True`
