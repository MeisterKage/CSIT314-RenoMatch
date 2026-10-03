import pytest

from app import create_app
from app.entity import db


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_home_page_shows_site_name(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"RenoMatch" in resp.data


def test_production_refuses_default_secret_key(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SEED_ON_EMPTY", "0")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()


def test_production_refuses_empty_secret_key(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SECRET_KEY", "")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SEED_ON_EMPTY", "0")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()


def test_production_sets_secure_cookie_flags(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SEED_ON_EMPTY", "0")
    app = create_app()
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    with app.app_context():
        db.engine.dispose()
