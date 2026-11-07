from tests.helpers import TEST_PASSWORD


def test_change_password_requires_login(client, default_profiles):
    assert client.get("/account/password").headers["Location"] == "/login"


def test_change_password_page_renders_for_logged_in_user(client, make_account, login):
    login(make_account().username)
    resp = client.get("/account/password")
    assert resp.status_code == 200
    assert b"Change password" in resp.data


def test_change_password_then_log_in_with_new_password(client, make_account, login):
    account = make_account()
    login(account.username)
    resp = client.post(
        "/account/password",
        data={
            "current_password": TEST_PASSWORD,
            "new_password": "N3wPassword",
            "confirm_password": "N3wPassword",
        },
    )
    assert resp.headers["Location"] == "/"
    client.post("/logout")
    assert login(account.username, "N3wPassword").headers["Location"] == "/"


def test_change_password_shows_errors(client, make_account, login):
    login(make_account().username)
    resp = client.post(
        "/account/password",
        data={
            "current_password": "wrong-password",
            "new_password": "N3wPassword",
            "confirm_password": "N3wPassword",
        },
    )
    assert resp.status_code == 200
    assert b"Current password is incorrect." in resp.data
