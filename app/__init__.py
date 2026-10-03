import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from app.entity import db

DEV_SECRET_KEY = "dev-only-not-secret"

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, template_folder="boundary/templates")
    app.config.from_mapping(
        SITE_NAME="RenoMatch",
        SECRET_KEY=os.environ.get("SECRET_KEY", DEV_SECRET_KEY),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "renomatch.db")
        ),
    )
    if test_config:
        app.config.update(test_config)
    if os.environ.get("RENDER") and app.config["SECRET_KEY"] == DEV_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production.")

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)

    from app.boundary import register_blueprints

    register_blueprints(app)

    with app.app_context():
        db.create_all()
    return app
