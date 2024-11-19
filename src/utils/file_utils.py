from typing import Tuple, Optional, Set
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
import hashlib
import magic
import logging
import shutil

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(
        self,
        upload_dir: str,
        allowed_extensions: Set[str],
        max_file_size: int
    ):
        self.upload_dir = upload_dir
        self.allowed_extensions = allowed_extensions
        self.max_file_size = max_file_size
        self.mime = magic.Magic(mime=True)

        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)

    def validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """Validate the uploaded file."""
        try:
            # Check if file exists
            if not file:
                return False, "No file provided"

            # Check filename
            if file.filename == '':
                return False, "No selected file"

            # Check extension
            if not self._allowed_extension(file.filename):
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"

            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)

            if size > self.max_file_size:
                max_mb = self.max_file_size / (1024 * 1024)
                return False, f"File too large. Maximum size: {max_mb}MB"

            # Check MIME type using the file content
            content = file.read(2048)
            file.seek(0)
            mime_type = self.mime.from_buffer(content)

            if not self._allowed_mime_type(mime_type):
                return False, f"Invalid file type: {mime_type}"

            return True, None

        except Exception as e:
            logger.error(f"File validation error: {str(e)}", exc_info=True)
            return False, f"Error validating file: {str(e)}"

    def save_uploaded_file(self, file: FileStorage, filename: str) -> Tuple[str, str]:
        """Save uploaded file and return (file_path, file_hash)."""
        try:
            # Create safe filename
            safe_filename = secure_filename(filename)
            file_path = os.path.join(self.upload_dir, safe_filename)

            # Calculate hash while saving
            file_hash = hashlib.sha256()
            file.seek(0)

            # Save file
            file.save(file_path)

            # Calculate hash from saved file to avoid memory issues with large files
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    file_hash.update(chunk)

            return file_path, file_hash.hexdigest()

        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            raise

    def cleanup_temp_files(self, *file_paths: str):
        """Clean up temporary files."""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Error cleaning up {path}: {str(e)}")

    def _allowed_extension(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

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