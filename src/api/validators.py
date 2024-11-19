from typing import Tuple, Optional, Set, Dict, Any
from werkzeug.datastructures import FileStorage
import magic
import os
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class RequestValidator:
    """Validator for API request data."""
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)

    def validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        Returns (is_valid, error_message).
        """
        try:
            # Check if file exists
            if not file:
                return False, "No file provided"

            # Check filename
            if file.filename == '':
                return False, "No selected file"

            # Check file extension
            if not self._allowed_extension(file.filename):
                return False, f"File type not allowed. Allowed types: {', '.join(current_app.config['ALLOWED_EXTENSIONS'])}"

            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > current_app.config['MAX_CONTENT_LENGTH']:
                max_mb = current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)
                return False, f"File too large. Maximum size: {max_mb}MB"

            # Check MIME type
            file_content = file.read(2048)  # Read first 2KB for MIME detection
            file.seek(0)
            mime_type = self.mime.from_buffer(file_content)
            
            if not self._allowed_mime_type(mime_type):
                return False, f"Invalid file type: {mime_type}"

            return True, None

        except Exception as e:
            logger.error(f"File validation error: {str(e)}", exc_info=True)
            return False, f"Error validating file: {str(e)}"

    def validate_batch(self, files: Dict[str, FileStorage]) -> Tuple[bool, Optional[str]]:
        """
        Validate batch upload request.
        Returns (is_valid, error_message).
        """
        try:
            if not files:
                return False, "No files submitted"

            if len(files) > current_app.config.get('MAX_BATCH_SIZE', 100):
                return False, f"Batch size exceeds maximum of {current_app.config.get('MAX_BATCH_SIZE', 100)} files"

            # Validate each file
            for filename, file in files.items():
                is_valid, error = self.validate_file(file)
                if not is_valid:
                    return False, f"Invalid file '{filename}': {error}"

            return True, None

        except Exception as e:
            logger.error(f"Batch validation error: {str(e)}", exc_info=True)
            return False, f"Error validating batch: {str(e)}"

    def validate_industry(self, industry: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate industry parameter.
        Returns (is_valid, error_message).
        """
        if not industry:
            return True, None  # Industry is optional

        valid_industries = current_app.config.get('VALID_INDUSTRIES', {
            'financial', 'healthcare', 'legal', 'insurance'
        })
        
        if industry not in valid_industries:
            return False, f"Invalid industry. Valid options: {', '.join(valid_industries)}"

        return True, None

    def _allowed_extension(self, filename: str) -> bool:
        """Check if file has an allowed extension."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

    def _allowed_mime_type(self, mime_type: str) -> bool:
        """Check if MIME type is allowed."""
        allowed_mimes = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png'
        }
        return mime_type in allowed_mimes

def validate_request(f):
    """Decorator for validating API requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        validator = RequestValidator()
        
        # Validate file upload
        if request.files:
            if 'file' in request.files:
                # Single file upload
                is_valid, error = validator.validate_file(request.files['file'])
                if not is_valid:
                    return jsonify({"error": error}), 400
            else:
                # Batch upload
                is_valid, error = validator.validate_batch(request.files)
                if not is_valid:
                    return jsonify({"error": error}), 400
        
        # Validate industry parameter
        if 'industry' in request.form:
            is_valid, error = validator.validate_industry(request.form['industry'])
            if not is_valid:
                return jsonify({"error": error}), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

# Rate limiting decorator
def rate_limit(limit: int = 100, period: int = 60):
    """
    Decorator for rate limiting requests.
    
    Args:
        limit: Maximum number of requests
        period: Time period in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP address or API key)
            client_id = request.headers.get('X-API-Key') or request.remote_addr
            
            # Check rate limit in Redis
            redis_client = current_app.extensions['redis']
            key = f"rate_limit:{client_id}"
            
            # Increment counter
            current = redis_client.incr(key)
            
            # Set expiry if this is the first request
            if current == 1:
                redis_client.expire(key, period)
            
            # Check if limit is exceeded
            if current > limit:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "period": period,
                    "retry_after": redis_client.ttl(key)
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Example usage in routes:
"""
@api.route('/classify', methods=['POST'])
@validate_request
@rate_limit(limit=100, period=60)
def classify_file():
    # Your route implementation
    pass
"""
