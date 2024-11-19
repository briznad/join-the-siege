import requests
import os
import json
from datetime import datetime
import pandas as pd

def test_documents(base_url="http://localhost:5000", files_dir="files"):
    """Test classification of multiple documents and generate a report."""

    results = []

    # Test individual synchronous classification
    print("Testing individual classification...")
    for filename in os.listdir(files_dir):
        file_path = os.path.join(files_dir, filename)

        # Test with and without industry hint
        for industry in [None, 'financial']:
            try:
                with open(file_path, 'rb') as f:
                    data = {'industry': industry} if industry else {}
                    response = requests.post(
                        f"{base_url}/classify",
                        files={'file': f},
                        data=data
                    )

                    result = response.json()
                    results.append({
                        'filename': filename,
                        'industry_hint': industry,
                        'classification': result.get('document_type'),
                        'confidence': result.get('confidence_score'),
                        'processing_time': response.elapsed.total_seconds(),
                        'success': response.status_code == 200,
                        'error': result.get('error'),
                        'method': 'sync'
                    })
            except Exception as e:
                results.append({
                    'filename': filename,
                    'industry_hint': industry,
                    'error': str(e),
                    'success': False,
                    'method': 'sync'
                })

    # Test batch classification
    print("\nTesting batch classification...")
    try:
        files = {
            f'file_{i}': open(os.path.join(files_dir, filename), 'rb')
            for i, filename in enumerate(os.listdir(files_dir))
        }

        # Submit batch
        response = requests.post(
            f"{base_url}/batch/submit",
            files=files,
            data={'industry': 'financial'}
        )

        if response.status_code == 202:
            batch_id = response.json()['batch_id']

            # Poll for results
            for _ in range(30):  # Wait up to 30 seconds
                response = requests.get(f"{base_url}/batch/{batch_id}/status")
                if response.json().get('status') == 'completed':
                    batch_results = response.json().get('results', [])
                    for doc in batch_results:
                        results.append({
                            'filename': doc.get('filename'),
                            'industry_hint': 'financial',
                            'classification': doc.get('document_type'),
                            'confidence': doc.get('confidence_score'),
                            'processing_time': doc.get('processing_time'),
                            'success': True,
                            'method': 'batch'
                        })
                    break

    finally:
        # Close all files
        for f in files.values():
            f.close()

    # Generate report
    df = pd.DataFrame(results)

    # Save detailed results
    report_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    df.to_csv(f'classification_results_{report_time}.csv', index=False)

    # Print summary
    print("\nClassification Results Summary:")
    print("-" * 50)
    print(f"Total documents tested: {len(os.listdir(files_dir))}")
    print(f"Successful classifications: {df['success'].sum()}")
    print(f"Average confidence score: {df['confidence'].mean():.2f}")
    print(f"Average processing time: {df['processing_time'].mean():.2f} seconds")

    # Print confidence scores by document type
    print("\nConfidence Scores by Document Type:")
    print(df.groupby('classification')['confidence'].agg(['mean', 'min', 'max']))

    # Print error summary if any
    errors = df[df['success'] == False]
    if not errors.empty:
        print("\nErrors encountered:")
        for _, row in errors.iterrows():
            print(f"{row['filename']}: {row['error']}")

if __name__ == "__main__":
    test_documents()
