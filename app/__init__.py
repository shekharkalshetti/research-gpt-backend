from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173"],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-User-Id"]
        }
    })

    return app
