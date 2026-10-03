import itertools

import pytest

from app import create_app
from app.entity import IDP, Category, UserAccount, UserProfile, db
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


@pytest.fixture
def make_category(app):
    counter = itertools.count(1)

    def _make(**fields):
        n = next(counter)
        values = {"name": f"Category {n}", "description": "Test category"}
        values.update(fields)
        category = Category(**values)
        db.session.add(category)
        db.session.commit()
        return category

    return _make


@pytest.fixture
def make_idp(make_account, make_category):
    def _make(designer=None, category=None, **fields):
        values = {
            "title": "Modern HDB living room",
            "style": "Modern",
            "property_type": "HDB",
            "budget": 45000,
            "location": "Tampines",
        }
        values.update(fields)
        idp = IDP(
            designer=designer or make_account(role="designer"),
            category=category or make_category(),
            **values,
        )
        db.session.add(idp)
        db.session.commit()
        return idp

    return _make


@pytest.fixture
def login(client):
    def _login(username, password=TEST_PASSWORD):
        return client.post("/login", data={"username": username, "password": password})

    return _login
