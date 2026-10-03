import itertools

import pytest

from app import create_app
from app.entity import UserAccount, UserProfile, db
from app.entity.user_profile import DEFAULT_PROFILE_NAMES
from tests.helpers import TEST_CONFIG, TEST_PASSWORD


@pytest.fixture
def app():
    app = create_app(TEST_CONFIG)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def default_profiles(app):
    return {
        role: UserProfile.create(name, role) for role, name in DEFAULT_PROFILE_NAMES.items()
    }


@pytest.fixture
def make_account(default_profiles):
    counter = itertools.count(1)

    def _make(role="customer", password=TEST_PASSWORD, **fields):
        n = next(counter)
        values = {
            "username": f"user{n}",
            "email": f"user{n}@example.com",
            "full_name": f"Test User {n}",
        }
        values.update(fields)
        return UserAccount.create(password=password, profile=default_profiles[role], **values)

    return _make
