class ClassificationError(Exception):
    """Base exception for classification errors."""
    pass

class ExtractionError(ClassificationError):
    """Exception raised when content extraction fails."""
    pass

class ValidationError(ClassificationError):
    """Exception raised when document validation fails."""
    pass

class UnsupportedFormatError(ClassificationError):
    """Exception raised when document format is not supported."""
    pass

class InvalidIndustryError(ClassificationError):
    """Exception raised when an invalid industry is specified."""
    pass

class ConfidenceError(ClassificationError):
    """Exception raised when confidence score is below threshold."""
    def __init__(self, score: float, threshold: float):
        self.score = score
        self.threshold = threshold
        super().__init__(f"Confidence score {score} below threshold {threshold}")

class ProcessingError(ClassificationError):
    """Exception raised when document processing fails."""
    pass

class StorageError(ClassificationError):
    """Exception raised when document storage operations fail."""
    pass

class BatchProcessingError(ClassificationError):
    """Exception raised when batch processing fails."""
    def __init__(self, batch_id: str, failed_docs: list):
        self.batch_id = batch_id
        self.failed_docs = failed_docs
        super().__init__(
            f"Batch {batch_id} failed for documents: {', '.join(failed_docs)}"
        )

class TimeoutError(ClassificationError):
    """Exception raised when processing exceeds time limit."""
    def __init__(self, timeout: int):
        self.timeout = timeout
        super().__init__(f"Processing exceeded timeout of {timeout} seconds")

class RetryableError(ClassificationError):
    """Exception for errors that should trigger a retry."""
    def __init__(self, message: str, retry_count: int = 0):
        self.retry_count = retry_count
        super().__init__(f"{message} (Retry count: {retry_count})")

class PermanentError(ClassificationError):
    """Exception for errors that should not be retried."""
    pass

class FileSizeError(ValidationError):
    """Exception raised when file size exceeds limit."""
    def __init__(self, size: int, limit: int):
        self.size = size
        self.limit = limit
        super().__init__(
            f"File size {size} bytes exceeds limit of {limit} bytes"
        )

class FileTypeError(ValidationError):
    """Exception raised for unsupported file types."""
    def __init__(self, file_type: str, supported_types: list):
        self.file_type = file_type
        self.supported_types = supported_types
        super().__init__(
            f"File type {file_type} not supported. Supported types: {', '.join(supported_types)}"
        )

class CorruptedFileError(ValidationError):
    """Exception raised when file is corrupted."""
    pass

class ContentExtractionError(ExtractionError):
    """Exception raised when content extraction fails."""
    def __init__(self, message: str, page_number: int = None):
        self.page_number = page_number
        if page_number:
            message = f"{message} (Page {page_number})"
        super().__init__(message)

class OCRError(ExtractionError):
    """Exception raised when OCR processing fails."""
    pass

class TableExtractionError(ExtractionError):
    """Exception raised when table extraction fails."""
    pass
