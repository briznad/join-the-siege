from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..core.queue.tasks import process_batch
from ..core.storage import DocumentStore
from ..utils.file_utils import BatchFileManager
from ..utils.logging import RequestLogger, AuditLogger, MetricsLogger
import uuid
import time
import logging

batch_api = Blueprint('batch_api', __name__)
logger = logging.getLogger(__name__)
request_logger = RequestLogger()
audit_logger = AuditLogger()
metrics_logger = MetricsLogger()

def _init_batch_manager():
    return BatchFileManager(
        upload_dir=current_app.config['UPLOAD_FOLDER'],
        allowed_extensions=current_app.config['ALLOWED_EXTENSIONS'],
        max_file_size=current_app.config['MAX_CONTENT_LENGTH'],
        max_batch_size=current_app.config.get('MAX_BATCH_SIZE', 100)
    )

@batch_api.route('/batch/submit', methods=['POST'])
def submit_batch():
    start_time = time.time()
    batch_id = str(uuid.uuid4())
    store = DocumentStore()
    document_ids = []

    try:
        if not request.files:
            return jsonify({"error": "No files submitted"}), 400

        batch_manager = _init_batch_manager()
        files = []

        for file in request.files.values():
            if file and file.filename:
                doc_id = str(uuid.uuid4())
                document_ids.append(doc_id)

                files.append({
                    "id": doc_id,
                    "filename": secure_filename(file.filename),
                    "content": file.read(),
                    "industry": request.form.get("industry")
                })

        if not files:
            return jsonify({"error": "No valid files in batch"}), 400

        # Validate batch
        validation_results = batch_manager.validate_batch(
            [(f["filename"], f["content"]) for f in files]
        )

        invalid_files = [r for r in validation_results if not r["valid"]]
        if invalid_files:
            return jsonify({
                "error": "Invalid files in batch",
                "invalid_files": invalid_files
            }), 400

        # Store documents
        for file in files:
            store.store_document(file["id"], {
                "filename": file["filename"],
                "industry": file["industry"],
                "status": "pending",
                "batch_id": batch_id,
                "submitted_at": time.time()
            })

        # Submit batch for processing
        process_batch.delay(batch_id, document_ids)

        # Log batch submission
        metrics_logger.log_batch_metrics(
            batch_id=batch_id,
            total_documents=len(files),
            successful=0,
            failed=0,
            total_time=(time.time() - start_time) * 1000
        )

        return jsonify({
            "batch_id": batch_id,
            "document_count": len(files),
            "status": "submitted",
            "document_ids": document_ids
        }), 202

    except Exception as e:
        logger.error(f"Error submitting batch: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@batch_api.route('/batch/<batch_id>/status', methods=['GET'])
def batch_status(batch_id):
    try:
        store = DocumentStore()
        documents = store.get_batch_documents(batch_id)

        if not documents:
            return jsonify({"error": "Batch not found"}), 404

        stats = {
            "total": len(documents),
            "completed": sum(1 for doc in documents if doc["status"] == "completed"),
            "failed": sum(1 for doc in documents if doc["status"] == "failed"),
            "pending": sum(1 for doc in documents if doc["status"] == "pending")
        }

        processing_time = None
        if stats["completed"] > 0:
            completed_docs = [doc for doc in documents if doc["status"] == "completed"]
            total_time = sum(doc.get("processing_time", 0) for doc in completed_docs)
            processing_time = total_time / stats["completed"]

        return jsonify({
            "batch_id": batch_id,
            "status": "completed" if stats["pending"] == 0 else "processing",
            "statistics": {
                **stats,
                "average_processing_time": processing_time
            },
            "documents": documents
        }), 200

    except Exception as e:
        logger.error(f"Error checking batch status: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@batch_api.route('/batch/<batch_id>/cancel', methods=['POST'])
def cancel_batch(batch_id):
    try:
        store = DocumentStore()
        documents = store.get_batch_documents(batch_id)

        if not documents:
            return jsonify({"error": "Batch not found"}), 404

        # Cancel all pending tasks
        for doc in documents:
            if doc["status"] == "pending":
                store.update_document_status(doc["id"], "cancelled")

        # Cancel batch task
        process_batch.AsyncResult(batch_id).revoke(terminate=True)

        # Log cancellation
        audit_logger.log_access(
            document_id=batch_id,
            user_id=request.headers.get('X-User-ID'),
            action='cancel_batch'
        )

        return jsonify({
            "batch_id": batch_id,
            "status": "cancelled"
        }), 200

    except Exception as e:
        logger.error(f"Error cancelling batch: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@batch_api.route('/batch/<batch_id>/retry', methods=['POST'])
def retry_batch(batch_id):
    try:
        store = DocumentStore()
        documents = store.get_batch_documents(batch_id)

        if not documents:
            return jsonify({"error": "Batch not found"}), 404

        # Collect failed document IDs
        failed_docs = [
            doc["id"] for doc in documents
            if doc["status"] in ["failed", "cancelled"]
        ]

        if not failed_docs:
            return jsonify({
                "batch_id": batch_id,
                "message": "No failed documents to retry"
            }), 200

        # Reset document statuses
        for doc_id in failed_docs:
            store.update_document_status(doc_id, "pending")

        # Submit new batch task
        process_batch.delay(batch_id, failed_docs)

        # Log retry
        audit_logger.log_access(
            document_id=batch_id,
            user_id=request.headers.get('X-User-ID'),
            action='retry_batch'
        )

        return jsonify({
            "batch_id": batch_id,
            "status": "retrying",
            "retrying_documents": len(failed_docs)
        }), 202

    except Exception as e:
        logger.error(f"Error retrying batch: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@batch_api.route('/batch/<batch_id>/results', methods=['GET'])
def batch_results(batch_id):
    try:
        store = DocumentStore()
        documents = store.get_batch_documents(batch_id)

        if not documents:
            return jsonify({"error": "Batch not found"}), 404

        results = []
        for doc in documents:
            if doc["status"] == "completed":
                results.append({
                    "document_id": doc["id"],
                    "filename": doc["filename"],
                    "document_type": doc.get("document_type"),
                    "confidence_score": doc.get("confidence_score"),
                    "processing_time": doc.get("processing_time"),
                    "metadata": doc.get("metadata", {})
                })

        return jsonify({
            "batch_id": batch_id,
            "total_documents": len(documents),
            "completed_documents": len(results),
            "results": results
        }), 200

    except Exception as e:
        logger.error(f"Error getting batch results: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
