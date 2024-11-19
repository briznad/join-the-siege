import os
import hashlib
import magic
import shutil
from typing import Optional, Tuple, Set, List, Dict
from pathlib import Path
import tempfile
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class FileManager:
    """Utility class for file operations."""
    
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
    
    def save_uploaded_file(
        self,
        file,
        filename: str,
        prefix: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Save uploaded file and return (file_path, file_hash).
        
        Args:
            file: File-like object
            filename: Original filename
            prefix: Optional prefix for saved filename
        
        Returns:
            Tuple containing (file_path, file_hash)
        """
        try:
            # Generate unique filename
            safe_filename = self.get_safe_filename(filename, prefix)
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Save file and calculate hash
            file_hash = hashlib.sha256()
            with open(file_path, 'wb') as f:
                for chunk in iter(lambda: file.read(8192), b''):
                    file_hash.update(chunk)
                    f.write(chunk)
            
            return file_path, file_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {str(e)}")
            raise
    
    def get_safe_filename(self, filename: str, prefix: Optional[str] = None) -> str:
        """
        Generate safe filename with timestamp and optional prefix.
        
        Args:
            filename: Original filename
            prefix: Optional prefix to add to filename
        
        Returns:
            Safe filename string
        """
        # Secure the filename
        filename = secure_filename(filename)
        
        # Get timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get extension
        ext = os.path.splitext(filename)[1].lower()
        
        # Create safe base name
        base_name = ''.join(c for c in os.path.splitext(filename)[0] 
                           if c.isalnum() or c in '-_')
        
        # Combine parts
        parts = []
        if prefix:
            parts.append(str(prefix))
        parts.extend([timestamp, base_name])
        
        return '_'.join(parts) + ext
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file against size and type restrictions.
        
        Args:
            file_path: Path to file to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            size = os.path.getsize(file_path)
            if size > self.max_file_size:
                return False, f"File size {size} exceeds maximum of {self.max_file_size}"

            # Check extension
            ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            if ext not in self.allowed_extensions:
                return False, f"Extension .{ext} not allowed"

            # Check MIME type
            mime_type = self.mime.from_file(file_path)
            if not self._is_mime_type_allowed(mime_type):
                return False, f"MIME type {mime_type} not allowed"

            return True, None

        except Exception as e:
            return False, str(e)
    
    def create_temp_copy(self, file_path: str) -> str:
        """
        Create temporary copy of file for processing.
        
        Args:
            file_path: Path to file to copy
        
        Returns:
            Path to temporary copy
        """
        try:
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, os.path.basename(file_path))
            shutil.copy2(file_path, temp_path)
            return temp_path
        except Exception as e:
            logger.error(f"Error creating temp copy of {file_path}: {str(e)}")
            raise
    
    def cleanup_temp_files(self, *file_paths: str):
        """
        Clean up temporary files and directories.
        
        Args:
            file_paths: Paths to files or directories to clean up
        """
        for path in file_paths:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                logger.warning(f"Error cleaning up {path}: {str(e)}")
    
    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        Get file information including size, type, and hash.
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary containing file information
        """
        try:
            stat = os.stat(file_path)
            
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(8192), b''):
                    file_hash.update(chunk)
            
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'mime_type': self.mime.from_file(file_path),
                'hash': file_hash.hexdigest()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            raise
    
    def _is_mime_type_allowed(self, mime_type: str) -> bool:
        """
        Check if MIME type is allowed.
        
        Args:
            mime_type: MIME type to check
        
        Returns:
            Boolean indicating if MIME type is allowed
        """
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

class BatchFileManager(FileManager):
    """Extended FileManager for batch operations."""
    
    def __init__(
        self,
        upload_dir: str,
        allowed_extensions: Set[str],
        max_file_size: int,
        max_batch_size: int = 100
    ):
        super().__init__(upload_dir, allowed_extensions, max_file_size)
        self.max_batch_size = max_batch_size
    
    def process_batch(
        self,
        files: List[Tuple[str, bytes]],
        prefix: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Process a batch of files.
        
        Args:
            files: List of (filename, content) tuples
            prefix: Optional prefix for saved files
        
        Returns:
            List of dictionaries containing file information
        """
        if len(files) > self.max_batch_size:
            raise ValueError(
                f"Batch size {len(files)} exceeds maximum {self.max_batch_size}"
            )
        
        results = []
        temp_files = []
        
        try:
            for filename, content in files:
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    temp_files.append(temp_file.name)
                    
                    # Move to final location
                    file_path, file_hash = self.save_uploaded_file(
                        open(temp_file.name, 'rb'),
                        filename,
                        prefix
                    )
                    
                    # Get file info
                    file_info = self.get_file_info(file_path)
                    results.append({
                        'original_filename': filename,
                        'saved_path': file_path,
                        'hash': file_hash,
                        **file_info
                    })
            
            return results
            
        finally:
            # Cleanup temporary files
            self.cleanup_temp_files(*temp_files)
    
    def validate_batch(self, files: List[Tuple[str, bytes]]) -> List[Dict[str, any]]:
        """
        Validate a batch of files before processing.
        
        Args:
            files: List of (filename, content) tuples
        
        Returns:
            List of dictionaries containing validation results
        """
        validation_results = []
        
        for filename, content in files:
            result = {
                'filename': filename,
                'valid': True,
                'errors': []
            }
            
            # Check file size
            if len(content) > self.max_file_size:
                result['valid'] = False
                result['errors'].append(
                    f'File size exceeds maximum of {self.max_file_size} bytes'
                )
            
            # Check extension
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            if ext not in self.allowed_extensions:
                result['valid'] = False
                result['errors'].append(f'Extension .{ext} not allowed')
            
            # Check MIME type
            mime_type = magic.from_buffer(content, mime=True)
            if not self._is_mime_type_allowed(mime_type):
                result['valid'] = False
                result['errors'].append(f'MIME type {mime_type} not allowed')
            
            validation_results.append(result)
        
        return validation_results

def create_nested_directory(base_path: str, *paths: str) -> str:
    """
    Create nested directory structure.
    
    Args:
        base_path: Base directory path
        paths: Additional path components
    
    Returns:
        Full path to created directory
    """
    full_path = os.path.join(base_path, *paths)
    os.makedirs(full_path, exist_ok=True)
    return full_path

def get_directory_size(directory: str) -> int:
    """
    Calculate total size of directory in bytes.
    
    Args:
        directory: Path to directory
    
    Returns:
        Total size in bytes
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    return total_size

def cleanup_old_files(
    directory: str,
    max_age_days: int,
    exclude_patterns: Optional[List[str]] = None
):
    """
    Remove files older than specified age.
    
    Args:
        directory: Directory to clean
        max_age_days: Maximum age of files in days
        exclude_patterns: List of patterns to exclude from cleanup
    """
    now = datetime.now()
    max_age = now.timestamp() - (max_age_days * 24 * 60 * 60)
    
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            
            # Check exclusions
            if exclude_patterns and any(
                pattern in filename for pattern in exclude_patterns
            ):
                continue
            
            # Check file age
            if os.path.getctime(file_path) < max_age:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing {file_path}: {str(e)}")
