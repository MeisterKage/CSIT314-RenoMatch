import pytest

from app import create_app


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
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()
