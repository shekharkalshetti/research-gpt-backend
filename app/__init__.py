from flask import Flask
from flask_cors import CORS
from app.api.research import research_api
from app.api.overview import overview_api


def create_app():
    app = Flask(__name__)

    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-User-Id"]
        }
    })

    app.register_blueprint(research_api)
    app.register_blueprint(overview_api)

    return app
