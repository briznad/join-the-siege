import pytest
from src.core.classifier import DocumentClassifier
from src.exceptions.classification import ClassificationError
from src.core.models.document import Document
import os

def test_classify_bank_statement(classifier, sample_files):
    """Test classification of bank statement."""
    result = classifier.classify(sample_files['bank_statement'], industry='financial')
    assert isinstance(result, Document)
    assert result.document_type == "bank_statement"
    assert result.confidence_score > 0.7
    assert result.metadata.get('has_tables', False)

def test_classify_medical_record(classifier, sample_files):
    """Test classification of medical record."""
    result = classifier.classify(sample_files['medical_record'], industry='healthcare')
    assert result.document_type == "medical_record"
    assert result.confidence_score > 0.7

def test_classify_without_industry(classifier, sample_files):
    """Test classification without specifying industry."""
    result = classifier.classify(sample_files['bank_statement'])
    assert result.document_type in ["bank_statement", "unknown"]

def test_invalid_file(classifier, temp_upload_dir):
    """Test classification of invalid file."""
    invalid_file = os.path.join(temp_upload_dir, "invalid.txt")
    with open(invalid_file, "w") as f:
        f.write("Invalid content")

    with pytest.raises(ClassificationError):
        classifier.classify(invalid_file)

def test_confidence_threshold(classifier, sample_files):
    """Test confidence score thresholds."""
    result = classifier.classify(sample_files['invoice'])
    assert 0 <= result.confidence_score <= 1

def test_multiple_industries(classifier, sample_files):
    """Test classification across different industries."""
    industries = ['financial', 'healthcare', 'legal']
    results = []

    for industry in industries:
        result = classifier.classify(sample_files['bank_statement'], industry=industry)
        results.append(result)

    # Should have different confidence scores for different industries
    confidence_scores = [r.confidence_score for r in results]
    assert len(set(confidence_scores)) > 1
