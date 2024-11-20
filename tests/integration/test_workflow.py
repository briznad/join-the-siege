import pytest
from src.core.classifier import DocumentClassifier
from src.core.queue.tasks import classify_document, process_batch
from src.core.models.document import Document
import time
import os

def test_end_to_end_classification(sample_files, classifier):
    """Test complete classification workflow."""
    # 1. Classify document
    result = classifier.classify(sample_files['bank_statement'], industry='financial')
    assert isinstance(result, Document)

    # 2. Extract content
    assert result.extracted_text is not None

    # 3. Verify classification
    assert result.document_type == "bank_statement"
    assert result.confidence_score > 0.7

    # 4. Check metadata
    assert result.metadata.get('mime_type')
    assert result.metadata.get('file_size')
    assert result.metadata.get('processed_at')

def test_async_classification(sample_files):
    """Test asynchronous classification workflow."""
    # 1. Submit classification task
    with open(sample_files['bank_statement'], 'rb') as f:
        task = classify_document.delay(
            file_data=f.read(),
            filename='bank_statement.docx',
            industry='financial'
        )

    # 2. Wait for result
    result = task.get(timeout=10)
    assert result['document_type'] == "bank_statement"
    assert result['confidence_score'] > 0.7

def test_batch_processing_workflow(sample_files):
    """Test batch processing workflow."""
    # 1. Prepare batch
    batch_files = []
    for name, path in sample_files.items():
        with open(path, 'rb') as f:
            batch_files.append({
                'content': f.read(),
                'filename': f'{name}.docx'
            })

    # 2. Submit batch
    task = process_batch.delay(
        batch_id='test_batch',
        document_ids=[f['filename'] for f in batch_files]
    )

    # 3. Wait for results
    results = task.get(timeout=30)
    assert len(results) == len(batch_files)

    # 4. Verify results
    for doc_id in results:
        assert doc_id in [f['filename'] for f in batch_files]

def test_error_handling_workflow(temp_upload_dir):
    """Test error handling in workflow."""
    # 1. Create invalid file
    invalid_path = os.path.join(temp_upload_dir, "invalid.docx")
    with open(invalid_path, "w") as f:
        f.write("Invalid content")

    # 2. Try to classify
    with pytest.raises(Exception):
        classifier = DocumentClassifier()
        classifier.classify(invalid_path)

    # 3. Try async classification
    with open(invalid_path, 'rb') as f:
        task = classify_document.delay(
            file_data=f.read(),
            filename='invalid.docx',
            industry='financial'
        )

    # 4. Verify error handling
    with pytest.raises(Exception):
        task.get(timeout=10)

def test_concurrent_processing(sample_files):
    """Test concurrent document processing."""
    # 1. Submit multiple tasks
    tasks = []
    for _ in range(5):
        with open(sample_files['bank_statement'], 'rb') as f:
            task = classify_document.delay(
                file_data=f.read(),
                filename='bank_statement.docx',
                industry='financial'
            )
            tasks.append(task)

    # 2. Wait for all results
    results = [task.get(timeout=10) for task in tasks]

    # 3. Verify all processed successfully
    assert len(results) == 5
    for result in results:
        assert result['document_type'] == "bank_statement"
        assert result['confidence_score'] > 0.7