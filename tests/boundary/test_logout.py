def test_logout_ends_the_session(client, make_account, login):
    login(make_account().username)
    resp = client.post("/logout")
    assert resp.headers["Location"] == "/"
    assert client.get("/customer/").headers["Location"] == "/login"


def test_logout_confirms_on_home_page(client, make_account, login):
    login(make_account().username)
    resp = client.post("/logout", follow_redirects=True)
    assert b"You have been logged out." in resp.data


def test_logout_only_accepts_post(client):
    assert client.get("/logout").status_code == 405
