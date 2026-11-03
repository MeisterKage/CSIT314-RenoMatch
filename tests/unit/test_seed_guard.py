import sqlite3

import pytest
from sqlalchemy import inspect

from app import create_app
from app.entity import UserAccountEntity, db
from app.seed import seed_database
from tests.helpers import TEST_CONFIG


def test_seed_refuses_a_database_that_has_accounts(make_account):
    make_account()
    with pytest.raises(RuntimeError, match="already has accounts"):
        seed_database()


def test_create_app_seeds_an_empty_database_when_enabled():
    app = create_app({**TEST_CONFIG, "SEED_ON_EMPTY": True})
    with app.app_context():
        assert db.session.query(UserAccountEntity).count() > 400
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def test_seed_reset_rebuilds_a_database_with_an_old_schema(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as old:
        old.execute("CREATE TABLE user_account (id INTEGER PRIMARY KEY, full_name TEXT)")
        old.execute("CREATE TABLE view_event (id INTEGER PRIMARY KEY)")
    old.close()
    config = {**TEST_CONFIG, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}", "SEED_ON_EMPTY": True}
    app = create_app(config)  # starts despite the old schema, without seeding
    result = app.test_cli_runner().invoke(args=["seed", "--reset"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())
        assert "view_event" not in tables
        assert "platform_activity" in tables
        assert db.session.query(UserAccountEntity).count() > 400
        db.session.remove()
        db.engine.dispose()


def test_seed_command_without_reset_on_seeded_db_exits_cleanly(app, make_account):
    make_account()
    result = app.test_cli_runner().invoke(args=["seed"])
    assert result.exit_code == 0
    assert "Database already seeded; use --reset to rebuild." in result.output
