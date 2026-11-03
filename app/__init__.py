import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import OperationalError

from app.entity import UserAccountEntity, db

DEV_SECRET_KEY = "dev-only-not-secret"

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="boundary/templates",
        static_folder="boundary/static",
    )
    app.config.from_mapping(
        SITE_NAME="RenoMatch",
        SECRET_KEY=os.environ.get("SECRET_KEY", DEV_SECRET_KEY),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "renomatch.db")
        ),
        SEED_ON_EMPTY=os.environ.get("SEED_ON_EMPTY", "1") == "1",
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=30 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if os.environ.get("RENDER"):
        if not app.config["SECRET_KEY"] or app.config["SECRET_KEY"] == DEV_SECRET_KEY:
            raise RuntimeError("SECRET_KEY must be set in production.")
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)

    from app.boundary import register_blueprints
    from app.seed import register_seed_command, seed_database

    register_blueprints(app)
    register_seed_command(app)

    with app.app_context():
        db.create_all()
        if app.config["SEED_ON_EMPTY"] and _has_no_accounts(app):
            seed_database()
    return app


def _has_no_accounts(app: Flask) -> bool:
    """True for an empty database. A database left with an older schema is not seeded,
    so that `flask --app app seed --reset` can still start and rebuild it."""
    try:
        return db.session.query(UserAccountEntity).first() is None
    except OperationalError:
        db.session.rollback()
        app.logger.warning(
            "The database schema is out of date. Run: flask --app app seed --reset"
        )
        return False
