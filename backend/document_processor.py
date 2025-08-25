import io
import uuid
from typing import List, Dict
import PyPDF2
from docx import Document
import re

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def process_document(self, content: bytes, filename: str) -> List[Dict]:
        """Process document and return chunks with metadata"""
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            text = self._extract_pdf_text(content)
        elif filename.lower().endswith('.docx'):
            text = self._extract_docx_text(content)
        elif filename.lower().endswith('.txt'):
            text = content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        # Clean and split text into chunks
        chunks = self._split_text(text)
        
        # Create chunk objects with metadata
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            chunk_objects.append({
                "content": chunk,
                "metadata": {
                    "filename": filename,
                    "chunk_id": i,
                    "chunk_uuid": str(uuid.uuid4())
                }
            })
        
        return chunk_objects
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error extracting PDF text: {str(e)}")
    
    def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error extracting DOCX text: {str(e)}")
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        # Clean text
        text = re.sub(r'\s+', ' ', text.strip())
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks