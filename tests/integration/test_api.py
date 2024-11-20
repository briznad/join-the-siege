import pytest
from flask import url_for
import json
import os
from src.api.app import app

@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_classify_endpoint(client, sample_files):
    """Test the /classify endpoint."""
    with open(sample_files['bank_statement'], 'rb') as f:
        data = {
            'file': (f, 'bank_statement.docx'),
            'industry': 'financial'
        }
        response = client.post(
            '/api/classify',
            data=data,
            content_type='multipart/form-data'
        )

    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'document_type' in result
    assert 'confidence_score' in result
    assert 'metadata' in result

def test_batch_endpoint(client, sample_files):
    """Test the /batch/submit endpoint."""
    files = []
    for name, path in sample_files.items():
        with open(path, 'rb') as f:
            files.append((f, f'{name}.docx'))

    data = {
        'files': files,
        'industry': 'financial'
    }
    response = client.post(
        '/api/batch/submit',
        data=data,
        content_type='multipart/form-data'
    )

    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'batch_id' in result
    assert 'document_count' in result
    assert result['status'] == 'submitted'

def test_invalid_file(client):
    """Test handling of invalid file upload."""
    data = {
        'file': ('invalid.txt', b'Invalid content'),
        'industry': 'financial'
    }
    response = client.post(
        '/api/classify',
        data=data,
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
    result = json.loads(response.data)
    assert 'error' in result

def test_missing_file(client):
    """Test handling of missing file."""
    response = client.post(
        '/api/classify',
        data={'industry': 'financial'},
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
    result = json.loads(response.data)
    assert 'error' in result
    assert 'No file part' in result['error']
