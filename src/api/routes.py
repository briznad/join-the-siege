from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..core.classifier import DocumentClassifier
from ..core.tasks import classify_document
from ..exceptions.classification_exceptions import ClassificationError
from ..utils.file_utils import FileManager
from ..utils.logging import RequestLogger, AuditLogger
import os
import time
import uuid
from typing import Optional

api = Blueprint('api', __name__)
request_logger = RequestLogger()
audit_logger = AuditLogger()

def _init_file_manager():
    return FileManager(
        upload_dir=current_app.config['UPLOAD_FOLDER'],
        allowed_extensions=current_app.config['ALLOWED_EXTENSIONS'],
        max_file_size=current_app.config['MAX_CONTENT_LENGTH']
    )

@api.before_request
def before_request():
    request.start_time = time.time()
    request.correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    request_logger.log_request(
        correlation_id=request.correlation_id,
        method=request.method,
        path=request.path,
        params=dict(request.args)
    )

@api.after_request
def after_request(response):
    request_logger.log_response(
        correlation_id=request.correlation_id,
        status_code=response.status_code,
        response_time=(time.time() - request.start_time) * 1000
    )
    return response

@api.route('/classify', methods=['POST'])
def classify_file():
    try:
        if 'file' not in request.files:
            return jsonify({
                "error": "No file part in the request",
                "allowed_extensions": list(current_app.config['ALLOWED_EXTENSIONS'])
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        file_manager = _init_file_manager()
        is_valid, error = file_manager.validate_file(file)
        if not is_valid:
            return jsonify({"error": error}), 400

        # Save file
        filename = secure_filename(file.filename)
        file_path, file_hash = file_manager.save_uploaded_file(file, filename)

        try:
            # Get industry from request if provided
            industry = request.form.get('industry')
            
            # Classify document
            classifier = DocumentClassifier()
            result = classifier.classify(file_path, industry=industry)
            
            # Log classification
            audit_logger.log_classification(
                document_id=file_hash,
                user_id=request.headers.get('X-User-ID'),
                document_type=result.document_type,
                confidence_score=result.confidence_score
            )
            
            # Prepare response
            response = {
                "document_id": file_hash,
                "document_type": result.document_type,
                "confidence_score": result.confidence_score,
                "metadata": {
                    "mime_type": result.mime_type,
                    "file_size": result.file_size,
                    "file_hash": result.file_hash,
                    "industry": result.industry,
                    "processed_at": result.processed_at.isoformat()
                }
            }
            
            if current_app.config.get('INCLUDE_EXTRACTED_TEXT', False):
                response["extracted_text"] = result.extracted_text

            return jsonify(response), 200

        finally:
            # Clean up uploaded file
            file_manager.cleanup_temp_files(file_path)

    except ClassificationError as e:
        request_logger.log_error(
            correlation_id=request.correlation_id,
            error=e
        )
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        request_logger.log_error(
            correlation_id=request.correlation_id,
            error=e
        )
        return jsonify({"error": "Internal server error"}), 500

@api.route('/classify/async', methods=['POST'])
def classify_file_async():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        file_manager = _init_file_manager()
        is_valid, error = file_manager.validate_file(file)
        if not is_valid:
            return jsonify({"error": error}), 400

        # Read file content and get industry
        file_content = file.read()
        industry = request.form.get('industry')
        
        # Submit async task
        task = classify_document.delay(
            file_content=file_content,
            filename=secure_filename(file.filename),
            industry=industry
        )
        
        return jsonify({
            "task_id": task.id,
            "status": "submitted"
        }), 202

    except Exception as e:
        request_logger.log_error(
            correlation_id=request.correlation_id,
            error=e
        )
        return jsonify({"error": "Internal server error"}), 500

@api.route('/classify/status/<task_id>', methods=['GET'])
def check_classification_status(task_id):
    task = classify_document.AsyncResult(task_id)
    
    if task.ready():
        if task.successful():
            return jsonify({
                "status": "completed",
                "result": task.get()
            }), 200
        else:
            return jsonify({
                "status": "failed",
                "error": str(task.result)
            }), 400
    
    return jsonify({
        "status": "processing",
        "progress": task.info.get('progress', 0) if task.info else 0
    }), 202

@api.route('/classify/preview/<document_id>', methods=['GET'])
def get_document_preview(document_id: str):
    try:
        file_manager = _init_file_manager()
        preview_path = os.path.join(current_app.config['PREVIEW_FOLDER'], f"{document_id}.png")
        
        if not os.path.exists(preview_path):
            return jsonify({"error": "Preview not found"}), 404
            
        return send_file(
            preview_path,
            mimetype='image/png',
            as_attachment=False,
            download_name=f"{document_id}_preview.png"
        )

    except Exception as e:
        request_logger.log_error(
            correlation_id=request.correlation_id,
            error=e
        )
        return jsonify({"error": "Internal server error"}), 500

@api.route('/classify/results/<document_id>', methods=['GET'])
def get_classification_results(document_id: str):
    try:
        # Get results from storage
        store = DocumentStore()
        result = store.get_document(document_id)
        
        if not result:
            return jsonify({"error": "Document not found"}), 404
            
        # Log access
        audit_logger.log_access(
            document_id=document_id,
            user_id=request.headers.get('X-User-ID'),
            action='view_results'
        )
        
        return jsonify(result), 200

    except Exception as e:
        request_logger.log_error(
            correlation_id=request.correlation_id,
            error=e
        )
        return jsonify({"error": "Internal server error"}), 500
