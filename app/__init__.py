from flask import Flask
from flask_cors import CORS
from .api import api, db
from config import Config


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    db.init_app(app)

    app.register_blueprint(api)
    return app
