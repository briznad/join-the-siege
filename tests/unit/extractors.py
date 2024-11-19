import pytest
from src.core.extractors.office import WordExtractor, ExcelExtractor
from src.core.extractors.base import ExtractedContent
import os

def test_word_extractor_supported_mimes(extractor_registry):
    """Test Word extractor MIME type support."""
    extractor = WordExtractor()
    assert 'application/msword' in extractor.supported_mimes
    assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in extractor.supported_mimes

def test_excel_extractor_supported_mimes(extractor_registry):
    """Test Excel extractor MIME type support."""
    extractor = ExcelExtractor()
    assert 'application/vnd.ms-excel' in extractor.supported_mimes
    assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in extractor.supported_mimes

def test_word_extraction(document_generator):
    """Test extraction of content from Word document."""
    extractor = WordExtractor()
    doc_path = document_generator._generate_bank_statement()['filepath']

    content = extractor.extract_content(doc_path)
    assert isinstance(content, ExtractedContent)
    assert content.text
    assert content.metadata
    if content.tables:
        assert isinstance(content.tables, list)

def test_excel_extraction(temp_upload_dir):
    """Test extraction of content from Excel document."""
    extractor = ExcelExtractor()

    # Create test Excel file
    import pandas as pd
    df = pd.DataFrame({
        'A': range(10),
        'B': range(10, 20)
    })
    excel_path = os.path.join(temp_upload_dir, "test.xlsx")
    df.to_excel(excel_path, index=False)

    content = extractor.extract_content(excel_path)
    assert isinstance(content, ExtractedContent)
    assert content.text
    assert content.tables
    assert len(content.tables) > 0

def test_invalid_word_document(temp_upload_dir):
    """Test handling of invalid Word document."""
    extractor = WordExtractor()
    invalid_path = os.path.join(temp_upload_dir, "invalid.docx")

    with open(invalid_path, "w") as f:
        f.write("Invalid content")

    with pytest.raises(Exception):
        extractor.extract_content(invalid_path)

def test_metadata_extraction(document_generator):
    """Test metadata extraction from documents."""
    extractor = WordExtractor()
    doc_path = document_generator._generate_medical_record()['filepath']

    content = extractor.extract_content(doc_path)
    assert 'page_count' in content.metadata
    assert 'word_count' in content.metadata
