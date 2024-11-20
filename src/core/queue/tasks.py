import base64
import tempfile
import os
from ..storage import DocumentStore
from typing import Optional
from .celery_config import celery_app
from ..classifier import DocumentClassifier
from ..models.document import Document
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='classify_document')
def classify_document(
    self,
    file_content: bytes,
    filename: str,
    industry: Optional[str] = None
) -> dict:
    """
    Celery task for asynchronous document classification.
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()

            try:
                # Classify document
                classifier = DocumentClassifier()
                result = classifier.classify(temp_file.name, industry=industry)

                return result.to_dict()

            finally:
                # Clean up temporary file
                os.unlink(temp_file.name)

    except Exception as e:
        logger.error(f"Document classification failed: {str(e)}", exc_info=True)
        raise

@celery_app.task(bind=True, name='process_batch')
def process_batch(self, batch_id: str, document_ids: list) -> list:
    """
    Process a batch of documents.
    """
    try:
        store = DocumentStore()
        results = []

        for doc_id in document_ids:
            document = store.get_document(doc_id)
            if document:
                try:
                    stringified = document['file_data']
                    decoded = base64.b64decode(stringified)
                    # Submit classification task

                    result = classify_document.delay(
                        decoded,
                        document['filename'],
                        document.get('industry')
                    )

                    # Update document status
                    store.update_document_status(
                        doc_id,
                        'processing',
                        task_id=result.id
                    )

                    results.append(doc_id)

                except Exception as e:
                    logger.error(
                        f"Failed to process document {doc_id}: {str(e)}",
                        exc_info=True
                    )
                    store.update_document_status(doc_id, 'failed')

        return results

    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        raise

