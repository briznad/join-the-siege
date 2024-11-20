import pytest
from src.core.extractors.office import WordExtractor, ExcelExtractor
from src.core.extractors.pdf import PDFExtractor
from src.core.extractors.image import ImageExtractor
from src.core.extractors.base import ExtractedContent
from src.exceptions.classification import ExtractionError
import os

@pytest.fixture
def extractors():
    return {
        'word': WordExtractor(),
        # 'excel': ExcelExtractor(),
        'pdf': PDFExtractor(),
        'image': ImageExtractor()
    }

def test_word_extractor_supported_mimes(extractors):
    """Test Word extractor MIME type support."""
    extractor = extractors['word']
    assert 'application/msword' in extractor.supported_mimes
    assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in extractor.supported_mimes

def test_excel_extractor_supported_mimes(extractors):
    """Test Excel extractor MIME type support."""
    extractor = extractors['excel']
    assert 'application/vnd.ms-excel' in extractor.supported_mimes
    assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in extractor.supported_mimes

def test_pdf_extractor_supported_mimes(extractors):
    """Test PDF extractor MIME type support."""
    extractor = extractors['pdf']
    assert 'application/pdf' in extractor.supported_mimes

def test_image_extractor_supported_mimes(extractors):
    """Test image extractor MIME type support."""
    extractor = extractors['image']
    assert 'image/jpeg' in extractor.supported_mimes
    assert 'image/png' in extractor.supported_mimes

def test_word_extraction(extractors, sample_files):
    """Test extraction of content from Word document."""
    extractor = extractors['word']
    content = extractor.extract_content(sample_files['bank_statement'])
    assert isinstance(content, ExtractedContent)
    assert content.text
    assert content.metadata
    if content.tables:
        assert isinstance(content.tables, list)

def test_excel_extraction(extractors, sample_files):
    """Test extraction of content from Excel document."""
    extractor = extractors['excel']
    content = extractor.extract_content(sample_files['financial_report'])
    assert isinstance(content, ExtractedContent)
    assert content.text
    assert content.tables
    assert len(content.tables) > 0

def test_pdf_extraction(extractors, sample_files):
    """Test extraction of content from PDF document."""
    extractor = extractors['pdf']
    content = extractor.extract_content(sample_files['invoice'])
    assert isinstance(content, ExtractedContent)
    assert content.text
    assert content.metadata.get('page_count')

def test_image_extraction(extractors, sample_files):
    """Test extraction of content from image."""
    extractor = extractors['image']
    content = extractor.extract_content(sample_files['drivers_license'])
    assert isinstance(content, ExtractedContent)
    assert content.text
    assert content.metadata.get('width')
    assert content.metadata.get('height')

def test_invalid_file_handling(extractors, temp_upload_dir):
    """Test handling of invalid files for each extractor."""
    invalid_file = os.path.join(temp_upload_dir, "invalid.txt")
    with open(invalid_file, "w") as f:
        f.write("Invalid content")

    for name, extractor in extractors.items():
        with pytest.raises(ExtractionError):
            extractor.extract_content(invalid_file)

def test_extraction_metadata(extractors, sample_files):
    """Test metadata extraction for each file type."""
    for name, extractor in extractors.items():
        if name == 'word':
            file_path = sample_files['bank_statement']
        elif name == 'excel':
            file_path = sample_files['financial_report']
        elif name == 'pdf':
            file_path = sample_files['invoice']
        else:  # image
            file_path = sample_files['drivers_license']

        content = extractor.extract_content(file_path)
        assert content.metadata is not None
        assert isinstance(content.metadata, dict)

def test_table_extraction(extractors, sample_files):
    """Test table extraction capabilities."""
    # Test Word tables
    word_content = extractors['word'].extract_content(sample_files['bank_statement'])
    assert word_content.tables is not None

    # Test Excel tables
    excel_content = extractors['excel'].extract_content(sample_files['financial_report'])
    assert excel_content.tables is not None
    assert len(excel_content.tables) > 0

def test_extractor_validation(extractors, sample_files):
    """Test file validation for each extractor."""
    for name, extractor in extractors.items():
        if name == 'word':
            file_path = sample_files['bank_statement']
        elif name == 'excel':
            file_path = sample_files['financial_report']
        elif name == 'pdf':
            file_path = sample_files['invoice']
        elif name == 'image':
            file_path = sample_files['drivers_license']

        print(f'Validating {name}, extractor { extractor }, for file: {file_path}')

        assert extractor.validate_file(file_path)