from app import create_app
from tests.helpers import TEST_CONFIG


def test_mail_settings_are_read_from_the_environment(monkeypatch):
    for key, value in {
        "MAIL_SERVER": "smtp.example.com",
        "MAIL_PORT": "587",
        "MAIL_USERNAME": "mailer",
        "MAIL_PASSWORD": "secret",
        "MAIL_SENDER": "noreply@example.com",
    }.items():
        monkeypatch.setenv(key, value)
    app = create_app(dict(TEST_CONFIG))
    assert app.config["MAIL_SERVER"] == "smtp.example.com"
    assert app.config["MAIL_SENDER"] == "noreply@example.com"


def test_mail_settings_default_to_empty_so_emails_are_logged(monkeypatch):
    monkeypatch.delenv("MAIL_SERVER", raising=False)
    assert not create_app(dict(TEST_CONFIG)).config["MAIL_SERVER"]
