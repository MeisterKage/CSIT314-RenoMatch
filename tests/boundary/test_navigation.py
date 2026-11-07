"""Role home pages and the header navigation: every link is real and resolves."""

import re

import pytest

NAV_LINKS = {
    "customer": ["Browse", "Favourites", "Compare (0)", "Enquiries", "Account"],
    "designer": ["Portfolio", "Dashboard", "Enquiries", "Company", "Account"],
    "admin": ["Accounts", "Profiles", "Audit log", "Account"],
    "platform": ["Categories", "Reports", "Reported", "Featured", "Account"],
}
HOMES = {
    "customer": "/",
    "designer": "/designer/",
    "admin": "/admin/",
    "platform": "/platform/",
}
MAIN_NAV = re.compile(r'<nav class="site-nav".*?</nav>', re.S)
HREF = re.compile(r'href="([^"]+)"')
TOOL_HREF = re.compile(r'<li class="tool[^"]*">\s*<h3><a href="([^"]+)"')


def navLabels(page):
    nav = MAIN_NAV.search(page).group(0)
    return [re.sub(r"\s+", " ", text).strip() for text in re.findall(r">([^<]+)</a>", nav)]


def paths(page, pattern):
    found = pattern.findall(MAIN_NAV.search(page).group(0) if pattern is HREF else page)
    return sorted({href.split("#")[0] for href in found if not href.startswith("#")})


@pytest.mark.parametrize("role", NAV_LINKS)
def test_nav_links_per_role_are_concise(client, make_account, login, role):
    login(make_account(role=role).username)
    labels = navLabels(client.get(HOMES[role]).get_data(as_text=True))
    for label in NAV_LINKS[role]:
        assert label in labels
    assert "Log in" not in labels and "Create account" not in labels


def test_visitor_nav_keeps_public_links(client):
    labels = navLabels(client.get("/").get_data(as_text=True))
    assert {"Browse designs", "How it works", "Log in", "Create account"} <= set(labels)


def test_nav_has_a_details_menu_for_the_role_links(client, make_account, login):
    login(make_account(role="customer").username)
    page = client.get("/").get_data(as_text=True)
    assert '<details class="nav-menu"' in page


@pytest.mark.parametrize("role", NAV_LINKS)
def test_every_nav_link_and_home_tool_resolves(client, make_account, login, role):
    login(make_account(role=role).username)
    home = client.get(HOMES[role]).get_data(as_text=True)
    tools = paths(home, TOOL_HREF)
    assert tools or role == "customer", "the role home lists its tools as links"
    assert "Coming" not in home
    for href in set(paths(home, HREF)) | set(tools):
        assert client.get(href).status_code == 200, href


def test_visitor_nav_links_resolve(client):
    page = client.get("/").get_data(as_text=True)
    for href in paths(page, HREF):
        assert client.get(href).status_code == 200, href
