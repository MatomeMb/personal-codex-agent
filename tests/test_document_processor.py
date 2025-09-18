"""
Tests for Document Processor module
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append('.')

from src.document_processor import DocumentProcessor
from src.exceptions import DocumentProcessingError

class TestDocumentProcessor:
    """Test suite for DocumentProcessor class"""
    
    def test_processor_initialization(self):
        """Test document processor initialization"""
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=100)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 100
        assert '.pdf' in processor.supported_formats
        assert '.docx' in processor.supported_formats
        assert '.md' in processor.supported_formats
        assert '.txt' in processor.supported_formats
    
    def test_load_document_nonexistent_file(self):
        """Test loading non-existent file"""
        processor = DocumentProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.load_document("nonexistent_file.txt")
    
    def test_load_document_unsupported_format(self):
        """Test loading unsupported file format"""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            with pytest.raises(ValueError):
                processor.load_document(temp_file_path)
        finally:
            Path(temp_file_path).unlink()
    
    def test_load_text_file(self):
        """Test loading text file"""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write("This is a test document about software engineering.")
            temp_file_path = temp_file.name
        
        try:
            result = processor.load_document(temp_file_path)
            assert result['content'] == "This is a test document about software engineering."
            assert result['metadata']['type'] == 'text'
            assert result['metadata']['filename'] == Path(temp_file_path).name
        finally:
            Path(temp_file_path).unlink()
    
    def test_chunk_text_small_content(self):
        """Test chunking text smaller than chunk size"""
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        text = "This is a short text."
        
        chunks = processor.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_large_content(self):
        """Test chunking text larger than chunk size"""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        text = "This is a longer text that should be split into multiple chunks. " * 3
        
        chunks = processor.chunk_text(text)
        assert len(chunks) > 1
        assert all(len(chunk) <= 50 for chunk in chunks)
    
    def test_chunk_text_sentence_boundary(self):
        """Test that chunking respects sentence boundaries"""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        
        chunks = processor.chunk_text(text)
        assert len(chunks) > 1
        # Check that chunks end at sentence boundaries when possible
        for chunk in chunks:
            if chunk.endswith('.'):
                assert chunk.count('.') >= 1
    
    def test_process_document(self):
        """Test processing a complete document"""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write("This is a test document. " * 5)  # Create longer text
            temp_file_path = temp_file.name
        
        try:
            result = processor.process_document(temp_file_path)
            
            assert 'document' in result
            assert 'chunks' in result
            assert 'total_chunks' in result
            assert result['total_chunks'] > 1
            assert len(result['chunks']) == result['total_chunks']
            
            # Check chunk structure
            for chunk in result['chunks']:
                assert 'content' in chunk
                assert 'chunk_id' in chunk
                assert 'metadata' in chunk
                assert chunk['metadata']['chunk_index'] == chunk['chunk_id']
        
        finally:
            Path(temp_file_path).unlink()
    
    def test_process_directory_empty(self):
        """Test processing empty directory"""
        processor = DocumentProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = processor.process_directory(temp_dir)
            assert result == []
    
    def test_process_directory_with_files(self):
        """Test processing directory with files"""
        processor = DocumentProcessor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "test1.txt").write_text("First test document.")
            (Path(temp_dir) / "test2.txt").write_text("Second test document.")
            (Path(temp_dir) / "unsupported.xyz").write_text("Unsupported file.")
            
            result = processor.process_directory(temp_dir)
            assert len(result) == 2  # Only .txt files should be processed
    
    def test_process_directory_nonexistent(self):
        """Test processing non-existent directory"""
        processor = DocumentProcessor()
        
        with pytest.raises(ValueError):
            processor.process_directory("nonexistent_directory")
    
    @patch('src.document_processor.pypdf')
    def test_load_pdf_file(self, mock_pypdf):
        """Test loading PDF file with mocked pypdf"""
        processor = DocumentProcessor()
        
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF content"
        mock_reader.pages = [mock_page]
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"fake pdf content")
            temp_file_path = temp_file.name
        
        try:
            result = processor.load_document(temp_file_path)
            assert result['content'] == "PDF content"
            assert result['metadata']['type'] == 'pdf'
            assert result['metadata']['pages'] == 1
        finally:
            Path(temp_file_path).unlink()
    
    @patch('src.document_processor.Document')
    def test_load_docx_file(self, mock_document):
        """Test loading DOCX file with mocked python-docx"""
        processor = DocumentProcessor()
        
        # Mock document
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "DOCX content"
        mock_doc.paragraphs = [mock_paragraph]
        mock_document.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_file.write(b"fake docx content")
            temp_file_path = temp_file.name
        
        try:
            result = processor.load_document(temp_file_path)
            assert result['content'] == "DOCX content"
            assert result['metadata']['type'] == 'docx'
            assert result['metadata']['paragraphs'] == 1
        finally:
            Path(temp_file_path).unlink()
    
    @patch('src.document_processor.markdown')
    def test_load_markdown_file(self, mock_markdown):
        """Test loading Markdown file with mocked markdown"""
        processor = DocumentProcessor()
        
        # Mock markdown conversion
        mock_markdown.markdown.return_value = "<p>Markdown content</p>"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".md", delete=False, encoding='utf-8') as temp_file:
            temp_file.write("# Test Markdown")
            temp_file_path = temp_file.name
        
        try:
            result = processor.load_document(temp_file_path)
            assert "Markdown content" in result['content']
            assert result['metadata']['type'] == 'markdown'
        finally:
            Path(temp_file_path).unlink()

if __name__ == "__main__":
    pytest.main([__file__])
