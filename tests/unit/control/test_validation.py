import pytest

from app.control.validation import (
    email_problem,
    password_problem,
    phone_problem,
    username_problem,
)


@pytest.mark.parametrize(
    "value, ok",
    [("abc", True), ("user_01", True), ("ab", False), ("a" * 31, False), ("bad name", False)],
)
def test_username_rule(value, ok):
    assert (username_problem(value) is None) == ok


@pytest.mark.parametrize(
    "value, ok",
    [("a@b.co", True), ("no-at-sign", False), ("a@b", False), ("a b@c.com", False)],
)
def test_email_rule(value, ok):
    assert (email_problem(value) is None) == ok


@pytest.mark.parametrize(
    "value, ok",
    [("Passw0rd", True), ("Short1a", False), ("allletters", False), ("12345678", False)],
)
def test_password_rule(value, ok):
    assert (password_problem(value) is None) == ok


@pytest.mark.parametrize(
    "value, ok",
    [("", True), ("+65 9123 4567", True), ("91234567", True), ("abc", False), ("123", False)],
)
def test_phone_rule(value, ok):
    assert (phone_problem(value) is None) == ok
