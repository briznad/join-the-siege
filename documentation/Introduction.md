# Document Classifier

A scalable, extensible document classification system that supports multiple file formats and industries. The system uses a combination of text analysis, pattern matching, and industry-specific rules to classify documents accurately.

## Key Features

- Multi-format support (PDF, Word, Excel, Images)
- Industry-specific classification strategies
- High-volume batch processing
- Comprehensive monitoring and logging
- Extensible architecture
- REST API interface

## How It Works

The classifier uses a three-stage approach:

1. **Content Extraction**
   - Extracts text and structural information from documents
   - Handles different file formats (PDF, Word, Excel, Images)
   - Uses OCR for image-based documents
   - Identifies tables, headers, and footers

2. **Classification**
   - Industry-specific strategies for targeted classification
   - Keyword matching and pattern recognition
   - Custom rules for specific document types
   - Confidence scoring

3. **Result Enhancement**
   - Metadata extraction
   - Table analysis
   - Format-specific feature detection
   - Confidence score calculation

## Quick Start

### Local Development

1. Clone the repository and install dependencies:
```bash
git clone https://github.com/briznad/join-the-siege.git
cd join-the-siege
pip install -e ".[dev]"
```

2. Start Redis (required for task queue):
```bash
docker run -d -p 6379:6379 redis:alpine
```

3. Start the application:
```bash
# Terminal 1: Start the API server
export FLASK_APP=src.api.app:app
export FLASK_ENV=development
flask run

# Terminal 2: Start the Celery worker
celery -A src.core.tasks worker -l INFO
```

4. Classify a single document:
```python
import requests

# Classify a single document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/classify',
        files={'file': f},
        data={'industry': 'financial'}  # Optional
    )
print(response.json())
```

### Production Deployment

1. Build and start services using Docker Compose:
```bash
# Start core services
docker-compose up -d

# Start monitoring stack (optional)
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

2. Access services:
- API: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

3. Configure environment variables in `config/production.py`:
```python
REDIS_URL = 'redis://redis:6379/0'
UPLOAD_FOLDER = '/app/uploads'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
```

## API Usage

### Single Document Classification

```python
# Synchronous classification
response = requests.post(
    'http://localhost:5000/classify',
    files={'file': open('document.pdf', 'rb')},
    data={'industry': 'financial'}
)

# Asynchronous classification
response = requests.post(
    'http://localhost:5000/classify/async',
    files={'file': open('document.pdf', 'rb')},
    data={'industry': 'financial'}
)
task_id = response.json()['task_id']

# Check async task status
response = requests.get(f'http://localhost:5000/classify/status/{task_id}')
```

### Batch Processing

```python
# Submit batch of documents
files = {
    f'file_{i}': open(f'document_{i}.pdf', 'rb')
    for i in range(5)
}
response = requests.post(
    'http://localhost:5000/batch/submit',
    files=files,
    data={'industry': 'financial'}
)
batch_id = response.json()['batch_id']

# Check batch status
response = requests.get(f'http://localhost:5000/batch/{batch_id}/status')
```

## Extending the Classifier

### Adding New Industry Support

1. Create a new strategy file (e.g., `src/core/strategies/legal.py`):
```python
from typing import Dict, List, Optional
from .base import BaseIndustryStrategy

class LegalIndustryStrategy(BaseIndustryStrategy):
    @property
    def industry_name(self) -> str:
        return "legal"

    @property
    def document_types(self) -> List[str]:
        return ["contract", "agreement", "affidavit"]

    @property
    def keywords(self) -> Dict[str, List[str]]:
        return {
            "contract": ["agreement", "terms", "parties"],
            # ... more document types and keywords
        }
```

2. Register the strategy in `src/core/classifier.py`:
```python
from .strategies.legal import LegalIndustryStrategy

def _register_strategies(self):
    strategies = [
        FinancialIndustryStrategy,
        HealthcareIndustryStrategy,
        LegalIndustryStrategy  # Add new strategy
    ]
```

### Adding New File Format Support

1. Create a new extractor (e.g., `src/core/extractors/powerpoint.py`):
```python
from typing import List
from .base import BaseExtractor, ExtractedContent

class PowerPointExtractor(BaseExtractor):
    @property
    def supported_mimes(self) -> List[str]:
        return ['application/vnd.ms-powerpoint']

    def extract_content(self, file_path: str) -> ExtractedContent:
        # Implement extraction logic
        pass
```

2. Register the extractor in your application initialization.

## Monitoring and Maintenance

### Health Checks
```bash
# Check system health
curl http://localhost:5000/health

# Get detailed metrics
curl http://localhost:5000/metrics
```

### Log Access
```bash
# Application logs
tail -f logs/document_classifier.log

# Error logs
tail -f logs/document_classifier_error.log
```

### Performance Monitoring

1. Access Grafana (http://localhost:3000)
2. Import the default dashboard
3. Monitor:
   - Document processing rates
   - Classification accuracy
   - Error rates
   - System resource usage

## Best Practices

1. **Document Preparation**
   - Ensure documents are not password-protected
   - Use standard file formats
   - Keep file sizes reasonable (< 10MB for optimal performance)

2. **Production Deployment**
   - Use environment-specific configuration
   - Set up proper monitoring and alerting
   - Implement rate limiting for API endpoints
   - Use SSL/TLS for API security

3. **Performance Optimization**
   - Configure worker count based on available resources
   - Use batch processing for large volumes
   - Implement caching where appropriate
   - Monitor and adjust resource allocation

## Troubleshooting

Common issues and solutions:

1. **Classification Failures**
   - Check file format compatibility
   - Verify file is not corrupted
   - Review classification confidence scores
   - Check extraction quality for image-based documents

2. **Performance Issues**
   - Monitor worker queue sizes
   - Check system resource usage
   - Review batch sizes
   - Verify Redis connection

3. **Integration Problems**
   - Verify API endpoint URLs
   - Check authentication credentials
   - Validate request payload format
   - Review API response codes

## Support

For issues and feature requests:
1. Check the issue tracker
2. Review the documentation
3. Open a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
