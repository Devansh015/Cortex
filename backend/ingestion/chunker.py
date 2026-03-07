"""
Content chunking module.
Splits content into overlapping chunks suitable for semantic retrieval and memory.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Chunk:
    """Represents a single chunk of content."""
    
    index: int
    content: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "index": self.index,
            "content": self.content,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "metadata": self.metadata,
        }


class ChunkingStrategy:
    """Base class for chunking strategies."""
    
    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Chunk content according to strategy."""
        raise NotImplementedError


class SemanticChunker(ChunkingStrategy):
    """
    Chunk content semantically, preserving meaning and context.
    Uses sentence boundaries and semantic breaks.
    """
    
    def __init__(
        self,
        target_size: int = 512,
        overlap: int = 128,
        min_chunk_size: int = 100,
    ):
        """
        Initialize semantic chunker.
        
        Args:
            target_size: Target chunk size in characters
            overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size
        """
        self.target_size = target_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """
        Chunk content semantically.
        
        Args:
            content: Text content to chunk
            metadata: Metadata to include with chunks
        
        Returns:
            List of Chunk objects
        """
        if not content or not content.strip():
            return []
        
        # Split into semantic units (sentences and paragraphs)
        units = self._split_into_units(content)
        
        # Group units into chunks
        chunks = self._group_units_into_chunks(units)
        
        # Create Chunk objects
        chunk_objects = []
        char_position = 0
        
        for idx, chunk_text in enumerate(chunks):
            if not chunk_text.strip():
                continue
            
            start_pos = content.find(chunk_text, char_position)
            if start_pos == -1:
                start_pos = char_position
            
            end_pos = start_pos + len(chunk_text)
            char_position = end_pos - self.overlap
            
            chunk_metadata = {
                **metadata,
                "chunk_index": idx,
                "chunk_count": len(chunks),
                "chunk_size": len(chunk_text),
                "source_start": start_pos,
                "source_end": end_pos,
            }
            
            chunk_objects.append(
                Chunk(
                    index=idx,
                    content=chunk_text.strip(),
                    start_pos=start_pos,
                    end_pos=end_pos,
                    metadata=chunk_metadata,
                )
            )
        
        return chunk_objects
    
    def _split_into_units(self, content: str) -> List[str]:
        """Split content into semantic units (sentences)."""
        # Split on sentence boundaries
        # Pattern: . or ! or ? followed by space and capital letter, or end of string
        sentence_pattern = r"(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$"
        
        sentences = re.split(sentence_pattern, content)
        
        # Filter out empty sentences and preserve original punctuation
        units = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) >= 10:  # Minimum sentence length
                units.append(sentence)
        
        return units
    
    def _group_units_into_chunks(self, units: List[str]) -> List[str]:
        """Group units into chunks with overlap."""
        if not units:
            return []
        
        chunks = []
        current_chunk = ""
        
        i = 0
        while i < len(units):
            unit = units[i]
            
            # Add unit to current chunk
            if current_chunk:
                potential = current_chunk + " " + unit
            else:
                potential = unit
            
            # Check if we've exceeded target size
            if len(potential) > self.target_size and current_chunk:
                # Save current chunk
                chunks.append(current_chunk)
                
                # Start overlap - include part of previous units
                overlap_text = self._create_overlap(units, i)
                current_chunk = overlap_text + " " + unit
            else:
                current_chunk = potential
            
            i += 1
        
        # Add final chunk
        if current_chunk.strip():
            if len(current_chunk) >= self.min_chunk_size or not chunks:
                chunks.append(current_chunk)
            elif chunks:
                # Merge with previous chunk if too small
                chunks[-1] += " " + current_chunk
        
        return chunks
    
    def _create_overlap(self, units: List[str], current_idx: int) -> str:
        """Create overlap from previous units."""
        overlap_units = []
        overlap_length = 0
        
        # Go backwards from previous unit
        for i in range(current_idx - 1, -1, -1):
            unit = units[i]
            overlap_units.insert(0, unit)
            overlap_length += len(unit) + 1  # +1 for space
            
            if overlap_length > self.overlap:
                break
        
        return " ".join(overlap_units)


class FixedSizeChunker(ChunkingStrategy):
    """Chunk content by fixed character size with overlap."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 128,
    ):
        """
        Initialize fixed-size chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, content: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Chunk content by fixed size."""
        if not content or not content.strip():
            return []
        
        chunks = []
        content = content.strip()
        position = 0
        chunk_idx = 0
        
        while position < len(content):
            # Extract chunk
            chunk_end = min(position + self.chunk_size, len(content))
            chunk_text = content[position:chunk_end]
            
            # Try to split at sentence boundary
            if chunk_end < len(content):
                # Find last sentence boundary
                last_period = chunk_text.rfind(".")
                last_exclamation = chunk_text.rfind("!")
                last_question = chunk_text.rfind("?")
                
                last_boundary = max(last_period, last_exclamation, last_question)
                if last_boundary > self.chunk_size // 2:
                    chunk_text = chunk_text[:last_boundary + 1]
                    chunk_end = position + len(chunk_text)
            
            chunk_text = chunk_text.strip()
            if chunk_text:
                chunk_metadata = {
                    **metadata,
                    "chunk_index": chunk_idx,
                    "source_start": position,
                    "source_end": chunk_end,
                    "chunk_size": len(chunk_text),
                }
                
                chunks.append(
                    Chunk(
                        index=chunk_idx,
                        content=chunk_text,
                        start_pos=position,
                        end_pos=chunk_end,
                        metadata=chunk_metadata,
                    )
                )
                
                chunk_idx += 1
            
            # Move position with overlap
            position = chunk_end - self.overlap
            if position >= len(content):
                break
        
        return chunks


def create_chunker(
    strategy: str = "semantic",
    **kwargs
) -> ChunkingStrategy:
    """
    Factory function to create a chunker.
    
    Args:
        strategy: "semantic" or "fixed"
        **kwargs: Additional arguments for the chunker
    
    Returns:
        ChunkingStrategy instance
    """
    if strategy == "semantic":
        return SemanticChunker(**kwargs)
    elif strategy == "fixed":
        return FixedSizeChunker(**kwargs)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")


# Example usage
if __name__ == "__main__":
    # Sample text
    sample_text = """
    This is a sample document with multiple sentences.
    It contains important information about the topic.
    The system processes this content intelligently.
    
    Each chunk should preserve context and meaning.
    Overlapping text helps with semantic retrieval.
    The chunking strategy can be customized as needed.
    """
    
    # Test semantic chunker
    chunker = SemanticChunker(target_size=100, overlap=30)
    metadata = {
        "source": "test",
        "user_id": "user_123",
    }
    
    chunks = chunker.chunk(sample_text, metadata)
    
    print(f"Total chunks: {len(chunks)}\n")
    for chunk in chunks:
        print(f"Chunk {chunk.index}:")
        print(f"  Content: {chunk.content[:80]}...")
        print(f"  Length: {len(chunk.content)}\n")
