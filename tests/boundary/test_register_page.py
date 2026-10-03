from app.entity import UserAccount

FORM = {
    "username": "newuser",
    "email": "new@example.com",
    "password": "Passw0rd!",
    "confirm_password": "Passw0rd!",
    "full_name": "New User",
    "phone": "",
    "role": "customer",
}


def test_register_page_renders_for_anonymous_visitor(client, default_profiles):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b"Create an account" in resp.data


def test_register_creates_account_and_sends_user_to_login(client, default_profiles):
    resp = client.post("/register", data=FORM)
    assert resp.headers["Location"] == "/login"
    assert UserAccount.find_by_username("newuser").role == "customer"


def test_newly_registered_user_can_log_in(client, default_profiles, login):
    client.post("/register", data={**FORM, "role": "designer"})
    assert login("newuser").headers["Location"] == "/designer/"


def test_register_shows_errors_and_keeps_input_except_passwords(client, default_profiles):
    resp = client.post("/register", data={**FORM, "email": "bad"})
    assert resp.status_code == 200
    assert b"Enter a valid email address." in resp.data
    assert b'value="newuser"' in resp.data
    assert b"Passw0rd!" not in resp.data
