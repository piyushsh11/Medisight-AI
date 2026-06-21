import os

from flask import Flask, send_from_directory

from config import DATABASE_PATH, FRONTEND_DIR, MAX_CONTENT_LENGTH, UPLOAD_FOLDER
from models.db import db
from routes.api_routes import api_bp
from utils.helpers import ensure_directory


def create_app() -> Flask:
    app = Flask(__name__)
    ensure_directory(os.path.dirname(DATABASE_PATH))
    ensure_directory(UPLOAD_FOLDER)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    db.init_app(app)

    app.register_blueprint(api_bp)

    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:filename>")
    def serve_frontend(filename: str):
        return send_from_directory(FRONTEND_DIR, filename)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
