from flask import Flask
from .routes import api
from .batch_routes import batch_api
from ..core.config import get_settings

def create_app():
    app = Flask(__name__)

    # Load configuration
    settings = get_settings()
    app.config.from_object(settings)

    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(batch_api, url_prefix='/api/batch')

    return app

# Create application instance
app = create_app()
