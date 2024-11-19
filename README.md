# Document Classifier

A scalable document classification system that supports multiple industries and file formats.

## Background

For a detailed overview of this apps' objectives and capabilities, see the [Introduction]('documentation/Introduction.md') document.

For a comparison of how this extended version of the app improves over the previous, 2-file version, see the [Improvements]('documentation/Improvements.md') document.

## Installation

```bash
# Clone repository
git clone https://github.com/briznad/join-the-siege.git
cd join-the-siege

# Install package and dependencies
pip install -e ".[dev]"

# Start Redis (required for task queue)
docker run -d -p 6379:6379 redis:alpine

# Start services using Docker Compose
docker-compose up -d
```

## Quick Start

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

# Submit a batch of documents
files = {
    f'file_{i}': open(f'document_{i}.pdf', 'rb')
    for i in range(3)
}
response = requests.post(
    'http://localhost:5000/batch/submit',
    files=files
)
print(response.json())
```

## Testing

### Run Test Suite
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Test with Sample Documents
The repository includes sample documents for testing:
```
files/
├── bank_statement_1.pdf
├── bank_statement_2.pdf
├── bank_statement_3.pdf
├── drivers_licence_2.jpg
├── drivers_license_1.jpg
├── drivers_license_3.jpg
├── invoice_1.pdf
├── invoice_2.pdf
└── invoice_3.pdf
```

To test classification performance:

1. Use the provided test script:
```bash
# Run tests on sample documents
python test_documents.py

# Test against custom server
python test_documents.py --base-url http://your-server:5000

# Test different document set
python test_documents.py --files-dir /path/to/files
```

2. The script will:
   - Test individual document classification
   - Test batch processing
   - Generate performance reports
   - Output summary statistics

3. Results will be saved in `classification_results_[timestamp].csv` with:
   - Document names
   - Classification results
   - Confidence scores
   - Processing times
   - Success/failure status
   - Any errors encountered

Example output:
```
Classification Results Summary:
--------------------------------------------------
Total documents tested: 9
Successful classifications: 9
Average confidence score: 0.85
Average processing time: 1.23 seconds

Confidence Scores by Document Type:
                     mean   min   max
bank_statement       0.92  0.88  0.95
drivers_license     0.88  0.82  0.91
invoice             0.83  0.79  0.89
```

## Documentation

- [Introduction](documentation/Introduction.md) - System overview and usage guide
- [Improvements](documentation/Improvements.md) - Comparison with original implementation

## Configuration

Configure environment-specific settings in:
```
config/
├── development.py
├── production.py
└── testing.py
```

## Monitoring

Access monitoring dashboards:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## Contributing

1. Fork the repository
2. Create your feature branch
3. Run tests
4. Submit pull request

## Support

Open an issue for bug reports or feature requests.
