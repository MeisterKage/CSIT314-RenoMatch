from pathlib import Path



def test_site_stylesheet_is_served(client):
    with client.get("/static/site.css") as resp:
        assert resp.status_code == 200
        assert b"--charcoal" in resp.data


def test_pages_use_site_stylesheet_not_bootstrap(client):
    page = client.get("/").data
    assert b"/static/site.css" in page
    assert b"bootstrap" not in page


def test_home_page_shows_hero_photo_and_style_gallery(client):
    page = client.get("/").data
    assert b"img/hero-living.jpg" in page
    assert b"Browse by style" in page
    for style in (b"Japandi", b"Contemporary", b"Mid-Century", b"Industrial", b"Luxury"):
        assert style in page
    assert b"How it works" in page


def test_home_page_photos_are_served(client):
    with client.get("/static/img/hero-living.jpg") as resp:
        assert resp.status_code == 200
        assert resp.mimetype == "image/jpeg"


def test_pages_have_skip_link_to_main_content(client):
    page = client.get("/").data
    assert b'href="#main"' in page
    assert b'id="main"' in page


def test_no_separate_role_home_template_is_left():
    assert not (Path(__file__).parents[2] / "app/boundary/templates/role_home.html").exists()
