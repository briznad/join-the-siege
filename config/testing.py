from .base import BaseConfig

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for testing