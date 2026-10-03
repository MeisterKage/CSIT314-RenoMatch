import pytest

from app import create_app
from tests.helpers import TEST_CONFIG


@pytest.fixture
def app():
    yield create_app(TEST_CONFIG)


@pytest.fixture
def client(app):
    return app.test_client()
