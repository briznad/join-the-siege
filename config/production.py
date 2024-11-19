from .base import BaseConfig

class ProductionConfig(BaseConfig):
    # Production-specific overrides
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB in production
    WORKER_CONCURRENCY = 8

    # Security settings
    TESTING = False
    DEBUG = False