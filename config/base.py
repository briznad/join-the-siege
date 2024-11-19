class BaseConfig:
    DEBUG = False
    TESTING = False
    UPLOAD_FOLDER = "files/uploads"
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"}
    REDIS_URL = "redis://localhost:6379/0"
    LOG_LEVEL = "INFO"

    # Classification settings
    MIN_CONFIDENCE_SCORE = 0.6
    ENABLE_BATCH_PROCESSING = True
    MAX_BATCH_SIZE = 1000

    # Monitoring settings
    ENABLE_PROMETHEUS = True
    METRICS_PORT = 9090

    # Worker settings
    WORKER_CONCURRENCY = 4
    TASK_TIME_LIMIT = 3600
    MAX_RETRIES = 3
    RETRY_BACKOFF = True