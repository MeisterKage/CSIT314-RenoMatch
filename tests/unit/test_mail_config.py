import pytest

from app import create_app
from app.entity import db
from tests.helpers import TEST_CONFIG


@pytest.fixture
def makeApp():
    created = []

    def _make():
        app = create_app(dict(TEST_CONFIG))
        created.append(app)
        return app

    yield _make
    for app in created:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()


def test_mail_settings_are_read_from_the_environment(monkeypatch, makeApp):
    for key, value in {
        "MAIL_SERVER": "smtp.example.com",
        "MAIL_PORT": "587",
        "MAIL_USERNAME": "mailer",
        "MAIL_PASSWORD": "secret",
        "MAIL_SENDER": "noreply@example.com",
    }.items():
        monkeypatch.setenv(key, value)
    app = makeApp()
    assert app.config["MAIL_SERVER"] == "smtp.example.com"
    assert app.config["MAIL_SENDER"] == "noreply@example.com"


def test_mail_settings_default_to_empty_so_emails_are_logged(monkeypatch, makeApp):
    monkeypatch.delenv("MAIL_SERVER", raising=False)
    assert not makeApp().config["MAIL_SERVER"]
