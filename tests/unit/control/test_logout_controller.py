from app.control.logout_controller import LogoutController


def test_logout_clears_everything_in_the_session():
    session = {"account_id": 5, "theme": "dark"}
    LogoutController().logout(session)
    assert session == {}
