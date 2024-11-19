from typing import Optional
from dataclasses import dataclass
import os
from config.base import BaseConfig

def get_settings():
    """Get application settings from environment-specific config."""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        from config.production import ProductionConfig
        return ProductionConfig()
    elif env == 'testing':
        from config.testing import TestingConfig
        return TestingConfig()
    else:
        from config.development import DevelopmentConfig
        return DevelopmentConfig()
