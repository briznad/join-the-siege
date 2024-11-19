import pytest
from pathlib import Path
import tempfile
import shutil
from document_classifier.core.classifier import DocumentClassifier
from document_classifier.core.extractors.registry import ExtractorRegistry
from document_classifier.tools.data_generation.generator import DocumentGenerator

@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for file uploads."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_files_dir():
    """Path to test files directory."""
    return Path(__file__).parent / "test_files"

@pytest.fixture
def classifier():
    """Initialize classifier instance."""
    return DocumentClassifier()

@pytest.fixture
def extractor_registry():
    """Initialize extractor registry."""
    return ExtractorRegistry()

@pytest.fixture
def document_generator(temp_upload_dir):
    """Initialize document generator for test data."""
    return DocumentGenerator(temp_upload_dir)

@pytest.fixture
def sample_files(test_files_dir, document_generator):
    """Generate sample files for testing."""
    files = {
        'bank_statement': document_generator._generate_bank_statement()['filepath'],
        'medical_record': document_generator._generate_medical_record()['filepath'],
        'invoice': document_generator._generate_financial_document()['filepath']
    }
    return files
