import pytest
from pathlib import Path
import tempfile
import shutil
from src.core.classifier import DocumentClassifier
from src.core.extractors.registry import ExtractorRegistry
from src.tools.data_generation.generator import DocumentGenerator

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
	generator = document_generator
	files = {
		'bank_statement': generator._generate_bank_statement()['filepath'],
		'medical_record': generator._generate_medical_record()['filepath'],
		'invoice': generator._generate_invoice()['filepath'],
		'drivers_license': generator._generate_document('financial')['filepath'],
		'lab_report': generator._generate_lab_report()['filepath'],
		'prescription': generator._generate_prescription()['filepath']
	}
	yield files

	# Clean up generated files
	for filepath in files.values():
		try:
			Path(filepath).unlink(missing_ok=True)
		except Exception as e:
			print(f"Warning: Could not delete {filepath}: {e}")