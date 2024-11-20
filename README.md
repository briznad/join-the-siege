# Document Classifier

A scalable document classification system that supports multiple industries and file formats.

## Background

For a detailed overview of this apps' objectives and capabilities, see the [Introduction](documentation/Introduction.md) document.

For a comparison of how this extended version of the app improves over the previous, 2-file version, see the [Improvements](documentation/Improvements.md) document.

## Installation

```bash
# Clone repository
git clone https://github.com/briznad/join-the-siege.git
cd join-the-siege

# Start services using Docker Compose
docker-compose up -d
```

## Quick Start

```bash
# navigate to directory with test files
cd tests/files/

# let the classification begin
curl -X POST http://localhost:5000/api/classify \
  -F "file=@document.pdf" \
  -F "industry=financial" # optional
```

## Testing

### Create virtual environment and install dependencies (if not already done)
```bash
# create and activate Python virtual environment
python -m venv virtual_env
source virtual_env/bin/activate

# install dependencies
pip install --no-cache-dir -r requirements.txt

# install dev dependencies
pip install -e ".[dev]"
```

### Test with Sample Documents
The repository includes sample documents for testing:
```
files/
├── document.pdf
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
python tests/test_documents.py

# Test against custom server
python tests/test_documents.py --base-url http://[your-server]:5000

# Test different document set
python tests/test_documents.py --files-dir /path/to/files
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

### Run Test Suite
```bash
# Run all tests
pytest tests/

# Or run specific test categories
pytest tests/unit/
pytest tests/integration/
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

## Contributing

1. Fork the repository
2. Create your feature branch
3. Run tests
4. Submit pull request

## Support

Open an issue for bug reports or feature requests.
