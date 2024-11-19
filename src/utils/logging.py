import logging
import structlog
from typing import Optional
import sys
from datetime import datetime
import os
from logging.handlers import RotatingFileHandler
import json

def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure and return a structured logger.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Create logs directory if it doesn't exist
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create formatters
    json_formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s", "level":"%(levelname)s", '
        '"logger":"%(name)s", "message":"%(message)s"}'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log file specified)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    return logger

class RequestLogger:
    """Logger for API requests with correlation IDs."""
    
    def __init__(self, logger_name: str = "request_logger"):
        self.logger = setup_logger(logger_name)
        
    def log_request(
        self,
        correlation_id: str,
        method: str,
        path: str,
        params: dict = None,
        **kwargs
    ):
        """Log API request details."""
        self.logger.info(
            "api_request",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "params": params or {},
                **kwargs
            }
        )

    def log_response(
        self,
        correlation_id: str,
        status_code: int,
        response_time: float,
        **kwargs
    ):
        """Log API response details."""
        self.logger.info(
            "api_response",
            extra={
                "correlation_id": correlation_id,
                "status_code": status_code,
                "response_time_ms": response_time,
                **kwargs
            }
        )

    def log_error(
        self,
        correlation_id: str,
        error: Exception,
        **kwargs
    ):
        """Log error details."""
        self.logger.error(
            "api_error",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                **kwargs
            },
            exc_info=True
        )

class AuditLogger:
    """Logger for audit trail of document operations."""
    
    def __init__(self, logger_name: str = "audit_logger"):
        self.logger = setup_logger(
            logger_name,
            log_file="logs/audit.log"
        )
    
    def log_classification(
        self,
        document_id: str,
        user_id: Optional[str],
        document_type: str,
        confidence_score: float,
        **kwargs
    ):
        """Log document classification event."""
        self.logger.info(
            "document_classified",
            extra={
                "document_id": document_id,
                "user_id": user_id,
                "document_type": document_type,
                "confidence_score": confidence_score,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )

    def log_access(
        self,
        document_id: str,
        user_id: str,
        action: str,
        **kwargs
    ):
        """Log document access event."""
        self.logger.info(
            "document_accessed",
            extra={
                "document_id": document_id,
                "user_id": user_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
        )

class MetricsLogger:
    """Logger for performance metrics and statistics."""
    
    def __init__(self, logger_name: str = "metrics_logger"):
        self.logger = setup_logger(
            logger_name,
            log_file="logs/metrics.log"
        )
    
    def log_processing_time(
        self,
        document_id: str,
        processing_time: float,
        document_type: str,
        **kwargs
    ):
        """Log document processing time."""
        self.logger.info(
            "processing_time",
            extra={
                "document_id": document_id,
                "processing_time_ms": processing_time,
                "document_type": document_type,
                **kwargs
            }
        )

    def log_batch_metrics(
        self,
        batch_id: str,
        total_documents: int,
        successful: int,
        failed: int,
        total_time: float,
        **kwargs
    ):
        """Log batch processing metrics."""
        self.logger.info(
            "batch_metrics",
            extra={
                "batch_id": batch_id,
                "total_documents": total_documents,
                "successful": successful,
                "failed": failed,
                "total_time_ms": total_time,
                "average_time_ms": total_time / total_documents if total_documents > 0 else 0,
                **kwargs
            }
        )

# Example usage
if __name__ == "__main__":
    # Setup request logger
    request_logger = RequestLogger()
    request_logger.log_request(
        correlation_id="123",
        method="POST",
        path="/classify",
        params={"industry": "financial"}
    )
    
    # Setup audit logger
    audit_logger = AuditLogger()
    audit_logger.log_classification(
        document_id="doc123",
        user_id="user456",
        document_type="bank_statement",
        confidence_score=0.95
    )
    
    # Setup metrics logger
    metrics_logger = MetricsLogger()
    metrics_logger.log_processing_time(
        document_id="doc123",
        processing_time=150.5,
        document_type="bank_statement"
    )
