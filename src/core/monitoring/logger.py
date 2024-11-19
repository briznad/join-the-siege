import logging
import structlog
from typing import Any, Dict
import sys
from datetime import datetime
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def setup_structured_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> None:
    
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Application log handler
    app_handler = RotatingFileHandler(
        filename=log_path / f"{service_name}.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )

    # Error log handler
    error_handler = RotatingFileHandler(
        filename=log_path / f"{service_name}_error.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)

    # Access log handler
    access_handler = TimedRotatingFileHandler(
        filename=log_path / f"{service_name}_access.log",
        when="midnight",
        interval=1,
        backupCount=30
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Configure handlers
    handlers = [app_handler, error_handler, access_handler, console_handler]
    for handler in handlers:
        handler.setFormatter(
            logging.Formatter(
                '{"timestamp":"%(asctime)s", "level":"%(levelname)s", '
                '"logger":"%(name)s", "message":"%(message)s"}'
            )
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    for handler in handlers:
        root_logger.addHandler(handler)

class ServiceLogger:
    def __init__(self, service_name: str):
        self.logger = structlog.get_logger(service_name)
        self.service_name = service_name

    def info(self, event: str, **kwargs):
        self.logger.info(event, service=self.service_name, **kwargs)

    def error(self, event: str, **kwargs):
        self.logger.error(event, service=self.service_name, **kwargs)

    def warning(self, event: str, **kwargs):
        self.logger.warning(event, service=self.service_name, **kwargs)

    def debug(self, event: str, **kwargs):
        self.logger.debug(event, service=self.service_name, **kwargs)

class RequestContextLogger:
    def __init__(self, logger: ServiceLogger):
        self.logger = logger

    def log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        client_ip: str,
        **kwargs
    ):
        self.logger.info(
            "request_started",
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_ip,
            **kwargs
        )

    def log_response(
        self,
        request_id: str,
        status_code: int,
        response_time: float,
        **kwargs
    ):
        self.logger.info(
            "request_completed",
            request_id=request_id,
            status_code=status_code,
            response_time_ms=response_time,
            **kwargs
        )

class TaskLogger:
    def __init__(self, logger: ServiceLogger):
        self.logger = logger

    def log_task_start(self, task_id: str, task_name: str, **kwargs):
        self.logger.info(
            "task_started",
            task_id=task_id,
            task_name=task_name,
            **kwargs
        )

    def log_task_success(
        self,
        task_id: str,
        task_name: str,
        execution_time: float,
        **kwargs
    ):
        self.logger.info(
            "task_completed",
            task_id=task_id,
            task_name=task_name,
            execution_time_ms=execution_time,
            status="success",
            **kwargs
        )

    def log_task_failure(
        self,
        task_id: str,
        task_name: str,
        error: Exception,
        **kwargs
    ):
        self.logger.error(
            "task_failed",
            task_id=task_id,
            task_name=task_name,
            error_type=type(error).__name__,
            error_message=str(error),
            status="failed",
            **kwargs,
            exc_info=True
        )

class ExtractorLogger:
    def __init__(self, logger: ServiceLogger):
        self.logger = logger

    def log_extraction_start(
        self,
        document_id: str,
        extractor_type: str,
        **kwargs
    ):
        self.logger.info(
            "extraction_started",
            document_id=document_id,
            extractor_type=extractor_type,
            **kwargs
        )

    def log_extraction_result(
        self,
        document_id: str,
        extractor_type: str,
        success: bool,
        execution_time: float,
        **kwargs
    ):
        self.logger.info(
            "extraction_completed",
            document_id=document_id,
            extractor_type=extractor_type,
            success=success,
            execution_time_ms=execution_time,
            **kwargs
        )
