# Ingestion Pipeline - Quick Reference

## One-Liner Examples

```python
# Text input
from backend.ingestion import ingest_input
ingest_input("user_1", "I'm skilled in Python")

# GitHub
ingest_input("user_1", "https://github.com/openai/gpt-3")

# PDF
ingest_input("user_1", "/path/to/file.pdf")
```

## Response Structure

```
status: "success" or "error"
detected_input_type: "text_prompt" | "github_repo" | "pdf"
chunks_created: number
items_stored: number
metadata_summary:
  - source_type
  - category (for text: skill, interest, experience, project_idea, preference, knowledge)
  - content_length
  - word_count
  - timestamp
```

## Environment Setup

```bash
# Set Backboard credentials
export BACKBOARD_API_KEY="key_here"
export BACKBOARD_API_URL="https://api.backboard.io"

# Optional: GitHub token for higher rate limits
export GITHUB_TOKEN="token_here"
```

## Module Structure

```
input_detector.py      → Detects input type
text_processor.py      → Processes text, infers category
github_processor.py    → Fetches GitHub repo data
pdf_processor.py       → Extracts PDF text
chunker.py            → Splits content into chunks
backboard_client.py   → Stores in Backboard
ingestion_pipeline.py → Orchestrates everything
```

## Usage Patterns

### Pattern 1: Simple Ingestion
```python
result = ingest_input("user_id", "input_data")
if result["status"] == "success":
    print(f"Created {result['chunks_created']} chunks")
```

### Pattern 2: Custom Pipeline
```python
from backend.ingestion import IngestionPipeline
pipeline = IngestionPipeline(chunking_strategy="fixed")
result = pipeline.ingest("user_id", "input_data")
```

### Pattern 3: Direct Processor
```python
from backend.ingestion import TextPromptProcessor
processor = TextPromptProcessor()
result = processor.process("text here", "user_id")
```

### Pattern 4: Storage Only
```python
from backend.ingestion import BackboardMemoryAdapter
adapter = BackboardMemoryAdapter()
adapter.save_ingestion_result("user_id", "text_prompt", chunks, metadata)
```

### Pattern 5: Search
```python
adapter.search_memories("user_id", "query", source_type="text_prompt", limit=10)
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Input too short | Text < 5 chars | Provide longer input |
| Invalid GitHub URL | Malformed URL | Check URL format |
| PDF not found | File path wrong | Verify file path |
| Empty content | No text extracted | Check file content |
| API error | Network/auth issue | Check BACKBOARD_API_KEY |

## Text Categories (Auto-Detected)

- **skill**: "I know", "proficient", "expertise"
- **interest**: "interested", "passionate", "love"
- **experience**: "built", "worked", "implemented"
- **project_idea**: "planning", "thinking", "want to"
- **preference**: "prefer", "like", "favorite"
- **knowledge**: (default for others)

## Chunking Strategies

**Semantic** (default):
- Preserves meaning
- Splits at sentence boundaries
- Best for documents

**Fixed-Size**:
- Consistent chunk sizes
- No semantic awareness
- Faster for large volumes

## FastAPI Example

```python
from fastapi import FastAPI
from backend.ingestion import IngestionPipeline

app = FastAPI()
pipeline = IngestionPipeline()

@app.post("/ingest")
async def ingest(user_id: str, text: str):
    return pipeline.ingest(user_id, text)
```

## Testing with Local Storage

```python
from backend.ingestion import (
    IngestionPipeline,
    BackboardMemoryAdapter,
    LocalMemoryStore
)

# Use in-memory storage (no API needed)
store = LocalMemoryStore()
adapter = BackboardMemoryAdapter(store)
pipeline = IngestionPipeline(memory_adapter=adapter)
```

## File Structure

```
backend/ingestion/
├── __init__.py                 # Exports
├── config.py                   # Configuration
├── input_detector.py           # Type detection
├── text_processor.py           # Text processing
├── github_processor.py         # GitHub API
├── pdf_processor.py            # PDF extraction
├── chunker.py                  # Chunking logic
├── backboard_client.py         # Storage adapter
├── ingestion_pipeline.py       # Main orchestration
├── examples.py                 # Usage examples
├── config.py                   # Settings
├── README.md                   # Documentation
├── INGESTION_GUIDE.md          # Detailed guide
└── QUICK_REFERENCE.md          # This file
```

## Key Classes

### `IngestionPipeline`
```python
pipeline = IngestionPipeline()
result = pipeline.ingest(user_id, input_data, file_name)
```

### `TextPromptProcessor`
```python
processor = TextPromptProcessor()
result = processor.process(text, user_id)
```

### `GitHubProcessor`
```python
processor = GitHubProcessor(github_token="optional")
result = processor.process(repo_url, user_id)
```

### `PDFProcessor`
```python
processor = PDFProcessor()
result = processor.process(pdf_path, user_id, file_name)
```

### `BackboardMemoryAdapter`
```python
adapter = BackboardMemoryAdapter()
adapter.save_ingestion_result(user_id, type, chunks, metadata)
adapter.search_memories(user_id, query, source_type, limit)
```

## Configuration Values

```python
MIN_TEXT_LENGTH = 5                    # Minimum text input
SEMANTIC_CHUNK_SIZE = 512             # Target chunk size
SEMANTIC_CHUNK_OVERLAP = 128          # Overlap between chunks
PDF_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
PDF_MAX_PAGES = 500                   # Page limit
GITHUB_API_TIMEOUT = 10               # Seconds
```

## Return Value Keys

```
"status"              # "success" or "error"
"detected_input_type" # Input type
"chunks_created"      # Number of chunks
"items_stored"        # Stored count
"metadata_summary"    # Key metadata
"details"             # Full processing details
"error"               # Error message (if failed)
```

## Input Type Detection

| Input | Detected Type |
|-------|---------------|
| "Plain text here" | `text_prompt` |
| "https://github.com/..." | `github_repo` |
| "/path/to/file.pdf" | `pdf` |
| (file as bytes) | `pdf` or `file` |
| "https://example.com" | `url` |

## Performance Targets

- Text processing: < 10ms
- GitHub processing: 500ms - 2s
- PDF processing: 100ms - 2s  
- Chunking: < 50ms
- Total pipeline: < 5 seconds

## Debugging

```python
# Enable detailed logging
pipeline = IngestionPipeline(enable_logging=True)

# Check configuration
from backend.ingestion import IngestionConfig
config = IngestionConfig()
validation = config.validate()  # Returns issues list
```

## Integration Checklist

- [ ] Set BACKBOARD_API_KEY
- [ ] Set GITHUB_TOKEN (optional)
- [ ] Import IngestionPipeline
- [ ] Create pipeline instance
- [ ] Call pipeline.ingest()
- [ ] Handle errors
- [ ] Implement search (optional)
- [ ] Test with local storage first

---

**For full documentation**: See `INGESTION_GUIDE.md` and `README.md`
