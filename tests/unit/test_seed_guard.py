import pytest

from app import create_app
from app.entity import UserAccount, db
from app.seed import seed_database
from tests.helpers import TEST_CONFIG


def test_seed_refuses_a_database_that_has_accounts(make_account):
    make_account()
    with pytest.raises(RuntimeError, match="already has accounts"):
        seed_database()


def test_create_app_seeds_an_empty_database_when_enabled():
    app = create_app({**TEST_CONFIG, "SEED_ON_EMPTY": True})
    with app.app_context():
        assert db.session.query(UserAccount).count() > 400
        db.session.remove()
        db.drop_all()


def test_seed_command_without_reset_on_seeded_db_exits_cleanly(app, make_account):
    make_account()
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code == 0
    assert "Database already seeded; use --reset to rebuild." in result.output
