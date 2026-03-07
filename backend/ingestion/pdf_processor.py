"""
PDF processor module.
Extracts text content from PDF files with multi-page support.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


class PDFProcessor:
    """Process PDF files and extract text content."""
    
    def __init__(self):
        """Initialize the PDF processor."""
        if PyPDF2 is None:
            raise ImportError(
                "PyPDF2 is required for PDF processing. "
                "Install it with: pip install PyPDF2"
            )
        
        self.max_pages = 500  # Limit to prevent memory issues
        self.encoding_fallbacks = ["utf-8", "latin-1", "iso-8859-1"]
    
    def process(
        self,
        pdf_input: any,
        user_id: str,
        file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a PDF file and extract content.
        
        Args:
            pdf_input: Path to PDF file or bytes object
            user_id: The user ID for tracking
            file_name: Optional file name (used if pdf_input is bytes)
        
        Returns:
            Dict with:
            - content: Extracted text content
            - metadata: PDF metadata
            - validation: Validation results
        """
        
        # Determine input type and validate
        if isinstance(pdf_input, (str, Path)):
            validation = self._validate_pdf_file(pdf_input)
            if not validation["is_valid"]:
                return {
                    "content": "",
                    "metadata": {"error": validation["error"]},
                    "validation": validation,
                }
            pdf_path = str(pdf_input)
            file_name = file_name or Path(pdf_input).name
        elif isinstance(pdf_input, bytes):
            if not file_name:
                file_name = "uploaded_document.pdf"
            pdf_path = pdf_input
            validation = {"is_valid": True}
        else:
            return {
                "content": "",
                "metadata": {"error": "Invalid PDF input type"},
                "validation": {
                    "is_valid": False,
                    "error": "PDF input must be file path or bytes"
                },
            }
        
        try:
            # Extract text and metadata
            extracted_text, page_count, metadata = self._extract_pdf_content(pdf_path)
            
            if not extracted_text or extracted_text.strip() == "":
                return {
                    "content": extracted_text,
                    "metadata": {
                        "error": "No text content could be extracted from PDF",
                        "file_name": file_name,
                        "page_count": page_count,
                    },
                    "validation": validation,
                }
            
            # Build complete metadata
            full_metadata = {
                "source_type": "pdf",
                "file_name": file_name,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "page_count": page_count,
                "content_length": len(extracted_text),
                "word_count": len(extracted_text.split()),
                **metadata,  # Include any additional metadata from PDF
            }
            
            return {
                "content": extracted_text,
                "metadata": full_metadata,
                "validation": validation,
            }
        
        except Exception as e:
            return {
                "content": "",
                "metadata": {"error": f"PDF processing error: {str(e)}", "file_name": file_name},
                "validation": validation,
            }
    
    def _validate_pdf_file(self, file_path: any) -> Dict[str, Any]:
        """Validate that the file exists and is a PDF."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    "is_valid": False,
                    "error": f"File does not exist: {file_path}"
                }
            
            if file_path.suffix.lower() != ".pdf":
                return {
                    "is_valid": False,
                    "error": f"File is not a PDF: {file_path.suffix}"
                }
            
            file_size = file_path.stat().st_size
            
            # Check file size (limit to 50MB)
            if file_size > 50 * 1024 * 1024:
                return {
                    "is_valid": False,
                    "error": f"PDF file is too large: {file_size / (1024*1024):.2f}MB (max 50MB)"
                }
            
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                return {
                    "is_valid": False,
                    "error": "PDF file is not readable"
                }
            
            return {
                "is_valid": True,
                "file_size": file_size,
                "file_path": str(file_path),
            }
        
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"File validation error: {str(e)}"
            }
    
    def _extract_pdf_content(
        self,
        pdf_input: any,
    ) -> tuple[str, int, Dict[str, Any]]:
        """
        Extract text content from PDF.
        
        Returns:
            Tuple of (extracted_text, page_count, metadata)
        """
        try:
            # Handle both file path and bytes
            if isinstance(pdf_input, bytes):
                from io import BytesIO
                pdf_file = BytesIO(pdf_input)
            else:
                pdf_file = open(pdf_input, "rb")
            
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract metadata
                metadata = {}
                if pdf_reader.metadata:
                    metadata = {
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "creator": pdf_reader.metadata.get("/Creator", ""),
                        "producer": pdf_reader.metadata.get("/Producer", ""),
                    }
                
                page_count = len(pdf_reader.pages)
                
                # Limit page extraction
                pages_to_extract = min(page_count, self.max_pages)
                
                # Extract text from all pages
                extracted_text = ""
                for page_idx in range(pages_to_extract):
                    try:
                        page = pdf_reader.pages[page_idx]
                        text = page.extract_text()
                        if text:
                            extracted_text += f"\n--- Page {page_idx + 1} ---\n"
                            extracted_text += text
                    except Exception as e:
                        print(f"Error extracting page {page_idx + 1}: {e}")
                        continue
                
                # Add notice if pages were limited
                if page_count > self.max_pages:
                    metadata["extraction_notice"] = (
                        f"Only first {self.max_pages} pages extracted "
                        f"(total pages: {page_count})"
                    )
                
                return extracted_text, page_count, metadata
            
            finally:
                if not isinstance(pdf_input, bytes):
                    pdf_file.close()
        
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r"\n\n\n+", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        
        # Remove control characters
        text = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")
        
        return text.strip()


# Example usage
if __name__ == "__main__":
    processor = PDFProcessor()
    
    # Example (would need a real PDF file)
    # result = processor.process("example.pdf", user_id="user_123")
    # print(f"Content length: {len(result['content'])}")
    # print(f"Metadata: {result['metadata']}")
