import re

import pytest

from app import create_app
from app.entity import UserAccountEntity, UserProfileEntity, db
from app.entity.user_profile import DEFAULT_PROFILE_NAMES
from tests.helpers import TEST_CONFIG, TEST_PASSWORD


@pytest.fixture
def csrf_app():
    app = create_app({**TEST_CONFIG, "WTF_CSRF_ENABLED": True})
    with app.app_context():
        profiles = {
            role: UserProfileEntity.createUserProfile(name, role)
            for role, name in DEFAULT_PROFILE_NAMES.items()
        }
        UserAccountEntity.createUserAccount(
            username="csrfuser",
            email="csrfuser@example.com",
            password=TEST_PASSWORD,
            name="CSRF User",
            profile=profiles["customer"],
        )
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


def test_login_post_without_csrf_token_is_rejected(csrf_client):
    resp = csrf_client.post("/login", data={"username": "csrfuser", "password": TEST_PASSWORD})
    assert resp.status_code == 400


def test_login_post_with_csrf_token_is_accepted(csrf_client):
    get_resp = csrf_client.get("/login")
    match = re.search(rb'name="csrf_token" value="([^"]+)"', get_resp.data)
    token = match.group(1).decode()
    resp = csrf_client.post(
        "/login",
        data={"username": "csrfuser", "password": TEST_PASSWORD, "csrf_token": token},
    )
    assert resp.status_code == 302
