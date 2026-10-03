# Sprint 0 Foundations Implementation Plan

**Goal:** A deployed Flask skeleton with CI/CD, every entity table, 100+ rows of generated test data per main entity, and working login (US01), logout (US02), registration (US03) and change password (US44).

**Architecture:** Flask app factory in `app/`, split into `boundary/` (Flask `MethodView` classes plus Jinja templates), `control/` (one controller class per user story) and `entity/` (Flask-SQLAlchemy models that own their persistence). SQLite stores the data. GitHub Actions lints and tests every push, and deploys `main` to Render through a deploy hook.

**Tech Stack:** Python 3.12+, Flask 3.1, Flask-SQLAlchemy 3.1, Flask-WTF (CSRF), Faker, pytest, pytest-cov, ruff, gunicorn, GitHub Actions, Render.

**Spec:** `docs/specs/2026-10-03-renovation-platform-design.md`

**Sprint 0 window:** 3–11 Oct 2026. Demo at the Mon 12 Oct lab.

## Global Constraints

- Python: CI and Render use 3.12. Local machines may use 3.12 or newer.
- Layering: a boundary only reads input, calls one controller and renders the result. A controller only calls entities. An entity owns its data and its persistence. No layer is skipped.
- Each user story has exactly one controller class (`<Verb><Noun>Controller`) and one boundary class (a Flask `MethodView` named `<Something>Page` or `<Something>Action`).
- Suspend, archive and remove are flags. Rows are never deleted, except where the spec says otherwise (US57 anonymises).
- Passwords are stored only as `werkzeug.security` hashes. They are never logged or echoed back into a page.
- Timestamps are naive UTC from `app.entity.db.utcnow()`.
- Every form includes `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- TDD commit convention: `test(<ID>): ...` (tests only, CI goes red), then `feat(<ID>): ...` (CI goes green). Infrastructure tasks use `chore(...)`.
- Merge PRs with **merge commits** (`gh pr merge --merge`), never squash or rebase. Squashing erases the red-then-green history that is the TDD evidence.
- Test data: at least 100 rows per main entity. Every seeded account's password is `Password123!`.
- The site name is the placeholder `RenoMatch`, set once in `SITE_NAME`. The group can rename it there.

## Deviations from the spec (intentional)

- Seed logic lives in `app/seed.py` with a `flask seed` CLI command instead of `scripts/seed.py`, because the app has to import it to seed on startup.
- `IDPFlag` gets a `created_at` column, which the spec table omits. Moderation queues need it.
- Boundaries are Flask `MethodView` classes, so each one is a real class that can appear in class and sequence diagrams.

## B-C-E style (checked against the lecture notes)

The design was checked against Topic 4 ("Advanced UML", slides 15–23) in `docs/reference/` on 3 Oct, and it matches the lecture:

- **Entity:** "holds the data and is responsible for its persistence"; maps directly to database tables; some entities are transient (`PlatformReport` and `Recommender` later on).
- **Control:** "one control class per use case"; it "implements the sequence diagram messaging" and holds the business rules.
- **Boundary:** "actors interact only with boundary classes"; a boundary represents the UI and has no use-case behaviour of its own.
- **Diagrams:** label classes with the stereotypes `«boundary»`, `«control»` and `«entity»`. Sequence diagrams follow the lecture's ATM example: Actor → `: LoginPage` → `: LoginController` → `: UserAccount`.

## Execution order: local first, GitHub and Render later

GitHub and Render are deferred until the app runs locally. Do the tasks in this order:

**1 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11**, then **2 → 3**.

Until Task 2 creates the remote:

- Skip every `git push` and `git pull` line.
- Replace the PR and merge lines (`gh pr create`, `gh pr checks`, `gh pr merge`) with:
  ```bash
  git checkout main
  git merge --no-ff <branch-name> -m "Merge <branch-name>"
  git branch -d <branch-name>
  ```
  `--no-ff` keeps each branch's red-then-green commits visible in history, just as a GitHub merge commit would.
- TDD evidence for these tasks comes from the git log: each `test(...)` commit comes before the `feat(...)` commit that makes it pass. When Task 2 pushes, the full history goes to GitHub unchanged. Red CI runs only start with the first story after Task 2, so make sure that story's red run gets screenshotted.
- Task 7's step "check the live site's logs" and Task 11's "verify live" steps wait until Task 3 is done.

## File map

| Path | Responsibility |
|---|---|
| `app/__init__.py` | App factory: config, extensions, blueprints, create tables, seed when empty |
| `app/seed.py` | Test-data generator and the `flask seed` command |
| `app/entity/db.py` | Shared `db` object and `utcnow()` |
| `app/entity/*.py` | One module per entity (or per tightly coupled pair) |
| `app/control/errors.py` | `LoginError`, `ValidationError` |
| `app/control/validation.py` | Field rules shared by controllers |
| `app/control/<story>_controller.py` | One controller per story |
| `app/boundary/__init__.py` | Registers all blueprints |
| `app/boundary/auth_guard.py` | Loads the current account per request; `role_required` and `login_required` |
| `app/boundary/public.py` | Home page, health check |
| `app/boundary/auth.py` | Login, logout, register and change-password boundaries |
| `app/boundary/{admin,designer,customer,platform}.py` | One blueprint per role; Sprint 0 adds only each role's home page |
| `app/boundary/templates/` | Jinja templates |
| `tests/helpers.py` | `TEST_CONFIG`, `TEST_PASSWORD` |
| `tests/conftest.py` | Fixtures: `app`, `client`, `default_profiles`, `make_account`, `make_category`, `make_idp`, `login` |
| `tests/unit/entity/`, `tests/unit/control/`, `tests/boundary/` | Tests per layer |
| `.github/workflows/ci.yml` | Lint, test, deploy |
| `docs/meetings/TEMPLATE.md`, `evidence/README.md` | Process scaffolding |

## Local setup (every member, once)

```bash
cd CSIT314                                   # the repo folder
python -m venv .venv                         # Windows: py -m venv .venv
source .venv/Scripts/activate                # Windows Git Bash; macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt          # available after Task 1
```

All commands below assume the virtual environment is active and the shell is in the repo root.

---

### Task 1: Project scaffold and health check

**Files:**
- Create: `.gitignore`, `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `README.md`
- Create: `app/__init__.py`, `app/boundary/__init__.py`, `app/boundary/public.py`
- Create: `app/boundary/templates/base.html`, `app/boundary/templates/_nav.html`, `app/boundary/templates/public/home.html`
- Create: `docs/meetings/TEMPLATE.md`, `evidence/README.md`
- Create: `tests/__init__.py`, `tests/helpers.py`, `tests/conftest.py`, `tests/boundary/__init__.py`
- Test: `tests/boundary/test_public.py`

**Interfaces:**
- Consumes: nothing
- Produces: `create_app(test_config: dict | None = None) -> Flask`; module-level `csrf`; `DEV_SECRET_KEY`; endpoints `public.home` (`/`) and `public.health` (`/health`); `register_blueprints(app)`; template `base.html` with blocks `title` and `content`, which includes `_nav.html`; fixtures `app` and `client`; `tests.helpers.TEST_CONFIG`

This is the only task committed straight to `main`, because no remote exists yet.

- [ ] **Step 1: Create the tooling files**

`.gitignore`:
```gitignore
.venv/
__pycache__/
*.pyc
instance/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.env
# Course material: copyright UOW, kept out of the repo
docs/reference/
Project Specification.pdf
```

`requirements.txt`:
```text
Flask>=3.1,<4
Flask-SQLAlchemy>=3.1,<4
Flask-WTF>=1.2,<2
Faker>=30
gunicorn>=23
```

`requirements-dev.txt`:
```text
-r requirements.txt
pytest>=8
pytest-cov>=5
ruff>=0.6
```

`pyproject.toml`:
```toml
[project]
name = "renomatch"
version = "0.1.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F"]
```

Then install: `pip install -r requirements-dev.txt`

- [ ] **Step 2: Write the failing tests**

`tests/__init__.py` and `tests/boundary/__init__.py`: empty files.

`tests/helpers.py`:
```python
TEST_CONFIG = {
    "TESTING": True,
    "SECRET_KEY": "test-secret",
    "WTF_CSRF_ENABLED": False,
}
```

`tests/conftest.py`:
```python
import pytest

from app import create_app
from tests.helpers import TEST_CONFIG


@pytest.fixture
def app():
    yield create_app(TEST_CONFIG)


@pytest.fixture
def client(app):
    return app.test_client()
```

`tests/boundary/test_public.py`:
```python
import pytest

from app import create_app


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_home_page_shows_site_name(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"RenoMatch" in resp.data


def test_production_refuses_default_secret_key(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest`
Expected: collection error, `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: Write the implementation**

`app/__init__.py`:
```python
import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

DEV_SECRET_KEY = "dev-only-not-secret"

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, template_folder="boundary/templates")
    app.config.from_mapping(
        SITE_NAME="RenoMatch",
        SECRET_KEY=os.environ.get("SECRET_KEY", DEV_SECRET_KEY),
    )
    if test_config:
        app.config.update(test_config)
    if os.environ.get("RENDER") and app.config["SECRET_KEY"] == DEV_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production.")

    csrf.init_app(app)

    from app.boundary import register_blueprints

    register_blueprints(app)
    return app
```

`app/boundary/__init__.py`:
```python
def register_blueprints(app):
    from app.boundary import public

    app.register_blueprint(public.bp)
```

`app/boundary/public.py`:
```python
from flask import Blueprint, jsonify, render_template
from flask.views import MethodView

bp = Blueprint("public", __name__)


class HomePage(MethodView):
    def get(self):
        return render_template("public/home.html")


class HealthCheck(MethodView):
    def get(self):
        return jsonify(status="ok")


bp.add_url_rule("/", view_func=HomePage.as_view("home"))
bp.add_url_rule("/health", view_func=HealthCheck.as_view("health"))
```

`app/boundary/templates/base.html`:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}{{ config.SITE_NAME }}{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <nav class="navbar navbar-expand bg-body-tertiary mb-4">
    <div class="container">
      <a class="navbar-brand" href="{{ url_for('public.home') }}">{{ config.SITE_NAME }}</a>
      <div class="navbar-nav ms-auto align-items-center">
        {% include "_nav.html" %}
      </div>
    </div>
  </nav>
  <main class="container">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

`app/boundary/templates/_nav.html`: an empty file. Task 8 fills it.

`app/boundary/templates/public/home.html`:
```html
{% extends "base.html" %}
{% block content %}
<div class="py-5 text-center">
  <h1 class="display-5">{{ config.SITE_NAME }}</h1>
  <p class="lead">Find an interior designer whose past work matches your home and budget.</p>
</div>
{% endblock %}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest`
Expected: `3 passed`

Run: `ruff check .`
Expected: `All checks passed!`

- [ ] **Step 6: Add the process scaffolding and README**

`docs/meetings/TEMPLATE.md`:
```markdown
# Meeting YYYY-MM-DD: Sprint N <planning | review | retro | stand-up>

**Time and place:**
**Present:**
**Absent (reason):**
**Facilitator / minute-taker:**

## Agenda
1.

## Progress since last meeting
| Member | Done | In progress | Blocked by |
|---|---|---|---|

## Backlog and burndown snapshot
![Taiga snapshot](../../evidence/week-N/FILE.png)

## Discussion summary
-

## Decisions
-

## Action items
| Action | Owner | Due |
|---|---|---|
```

`evidence/README.md`:
```markdown
# Weekly evidence

One folder per week: `week-1/`, `week-2/`, and so on. At the end of every sprint, save:

- Taiga product backlog, sprint taskboard and burndown chart
- GitHub Actions: one red TDD run, the green run after it, and the latest deploy run
- The running app on Render, one screenshot per feature finished that sprint

Name files `YYYY-MM-DD-what.png`.
```

`README.md`:
````markdown
# RenoMatch

CSIT314 group project: a platform that matches renovation customers with interior designers.
Design spec: `docs/specs/2026-10-03-renovation-platform-design.md`.

## Setup

```bash
python -m venv .venv                 # Windows: py -m venv .venv
source .venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Run

```bash
flask --app app run --debug
```

Open http://127.0.0.1:5000.

## Test and lint

```bash
python -m pytest --cov=app
ruff check .
```

## Workflow

1. Create a branch per story: `feature/US07-suspend-account`.
2. Commit the failing tests first (`test(US07): ...`) and push. CI goes red.
3. Commit the implementation (`feat(US07): ...`) and push. CI goes green.
4. Open a PR and merge it with a **merge commit** once CI passes.
````

- [ ] **Step 7: Commit**

```bash
git add .gitignore requirements.txt requirements-dev.txt pyproject.toml README.md app tests docs/meetings evidence
git commit -m "chore: scaffold Flask app with health check"
```

---

### Task 2: GitHub repository, CI and branch protection

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: Task 1's `pytest` and `ruff` setup
- Produces: GitHub remote `origin`; a CI check named `test` that later tasks rely on to merge

> **Confirm with Shawn before running Step 2.** Creating the repository publishes the code. Ask for: the owner (personal account `MeisterKage` or a group organisation), the repo name, and public or private.
>
> - Private is safer for coursework. However, branch protection on a **private** repo needs GitHub Pro, which is free with the GitHub Student Developer Pack. Without Pro, either make the repo public or skip Step 5 and rely on team discipline.
> - Tutors may need access. Ask Shawn whether to add them as collaborators.

- [ ] **Step 1: Write the CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements*.txt
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Lint
        run: ruff check .
      - name: Test
        run: pytest --cov=app --cov-report=term-missing
```

```bash
git add .github/workflows/ci.yml
git commit -m "chore: add CI workflow (lint + tests)"
```

- [ ] **Step 2: Create the repository and push (after confirmation)**

```bash
gh repo create OWNER/REPO --private --source . --remote origin --push
```

Replace `OWNER/REPO` with Shawn's answer, and use `--public` if that was chosen.

- [ ] **Step 3: Verify CI passes**

```bash
gh run watch --exit-status
```
Expected: the `test` job completes successfully.

- [ ] **Step 4: Add teammates**

Shawn adds each member under GitHub → repo → Settings → Collaborators. Each member clones the repo and does the local setup above.

- [ ] **Step 5: Protect `main`**

```bash
gh api -X PUT repos/OWNER/REPO/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -F "required_status_checks[strict]=true" \
  -f "required_status_checks[contexts][]=test" \
  -F "enforce_admins=true" \
  -F "required_pull_request_reviews[required_approving_review_count]=0" \
  -F "restrictions=null"
```

Expected: JSON describing the protection. If it fails with `Upgrade to GitHub Pro`, see the note above this task.

Verify: `git commit --allow-empty -m "test protection" && git push` must be **rejected**. Then undo the local commit: `git reset --hard HEAD~1`.

- [ ] **Step 6: Evidence**

Screenshot the green Actions run and the branch protection settings page into `evidence/week-1/`. Commit them in the next task's branch.

---

### Task 3: Continuous deployment to Render

**Files:**
- Modify: `.github/workflows/ci.yml` (add the `deploy` job)
- Modify: `README.md` (add a Deployment section)

**Interfaces:**
- Consumes: Task 2's `test` job
- Produces: GitHub secret `RENDER_DEPLOY_HOOK_URL`; a `deploy` job that runs only on pushes to `main` after `test` passes; a live URL `https://<service>.onrender.com`

> Steps 1–3 happen in the Render dashboard. Walk Shawn through them live; don't do them on Shawn's behalf.
>
> **Decide which Render account to use first.** Shawn already hosts one project on Render. All free web services in a workspace share **750 free instance hours per month**, and hours are only used while a service is awake (spun-down services use none). If the hours run out, Render suspends **every** free service in that workspace, including the existing project, until the next month.
>
> - Check Render dashboard → Billing (or Usage) for how many free hours the existing project used last month.
> - If it's well under about 400 hours, the group project can share the workspace.
> - If it's close to 750, for example because an uptime pinger keeps it awake, host the group project on a teammate's Render account instead.

- [ ] **Step 1: Create the Render web service**

Render dashboard → New → Web Service → connect the GitHub repo, then set:

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Branch | `main` |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT "app:create_app()"` |
| Instance type | Free |
| Environment: `SECRET_KEY` | Output of `python -c "import secrets; print(secrets.token_hex(32))"` |
| Environment: `PYTHON_VERSION` | `3.12.10` (any 3.12.x that Render accepts) |

Use exactly one worker. Each worker would otherwise run `create_app()` and seed the same SQLite file at the same time.

- [ ] **Step 2: Turn off Render's auto-deploy**

Service → Settings → Build & Deploy → Auto-Deploy: **Off**. From now on, deploys only happen when CI passes.

- [ ] **Step 3: Store the deploy hook in GitHub**

Service → Settings → Deploy Hook → copy the URL. Then:
```bash
gh secret set RENDER_DEPLOY_HOOK_URL     # paste the URL when prompted
```

- [ ] **Step 4: Add the deploy job on a branch**

```bash
git checkout -b chore/cd-render
```

Append to `.github/workflows/ci.yml`, at the same indentation as `test:`:
```yaml
  deploy:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render deploy
        env:
          RENDER_DEPLOY_HOOK_URL: ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
        run: curl -fsS -X POST "$RENDER_DEPLOY_HOOK_URL"
```

Append to `README.md`:
```markdown
## Deployment

Every push to `main` that passes CI triggers a deploy to Render through a deploy hook
(GitHub secret `RENDER_DEPLOY_HOOK_URL`). Render's own auto-deploy is off.

The free plan wipes the disk on every deploy, restart and spin-down (after 15 idle minutes).
The app therefore re-creates its test data on startup. Anything created on the live site is
temporary.
```

- [ ] **Step 5: Merge and verify the deploy**

```bash
git add .github/workflows/ci.yml README.md
git add evidence/week-1 2>/dev/null || true    # Task 2 screenshots, if saved
git commit -m "chore: deploy main to Render after CI passes"
git push -u origin chore/cd-render
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
gh run watch --exit-status
```

Expected: the run on `main` shows `test` and then `deploy`, both green. After the Render dashboard shows the deploy as live:
```bash
curl https://<service>.onrender.com/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 6: Evidence**

Screenshot the Actions run with both jobs, the Render deploy log and the `/health` response into `evidence/week-1/`.

---

### Task 4: Database layer and user entities

**Files:**
- Create: `app/entity/__init__.py`, `app/entity/db.py`, `app/entity/user_profile.py`, `app/entity/user_account.py`, `app/entity/login_attempt.py`, `app/entity/password_reset_token.py`
- Modify: `app/__init__.py`, `tests/helpers.py`, `tests/conftest.py`
- Create: `tests/unit/__init__.py`, `tests/unit/entity/__init__.py`
- Test: `tests/unit/entity/test_user_profile.py`, `tests/unit/entity/test_user_account.py`

**Interfaces:**
- Consumes: `create_app` from Task 1
- Produces:
  - `app.entity.db.db` (`SQLAlchemy`) and `app.entity.db.utcnow() -> datetime`
  - `ROLE_TYPES = ("admin", "designer", "customer", "platform")`
  - `DEFAULT_PROFILE_NAMES: dict[str, str]`, mapping each role type to its default profile name
  - `UserProfile.create(name, role_type, description="") -> UserProfile` (raises `ValueError` for an unknown role); `UserProfile.find_by_name(name)`; `UserProfile.find_default_for_role(role_type) -> UserProfile | None`
  - `UserAccount.create(username, email, password, full_name, profile, phone="") -> UserAccount`; `find_by_id`, `find_by_username`, `find_by_email` (case-insensitive); `set_password`; `check_password -> bool`; `change_password(new)` (commits); `can_log_in() -> bool`; property `role -> str`
  - `LoginAttempt` and `PasswordResetToken` models
  - Fixtures `default_profiles` (dict of role → `UserProfile`) and `make_account(role="customer", password=TEST_PASSWORD, **fields)`; `tests.helpers.TEST_PASSWORD = "Passw0rd!"`

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b chore/user-entities
```

- [ ] **Step 2: Update the test helpers and fixtures**

`tests/helpers.py` (replace the whole file):
```python
TEST_PASSWORD = "Passw0rd!"

TEST_CONFIG = {
    "TESTING": True,
    "SECRET_KEY": "test-secret",
    "WTF_CSRF_ENABLED": False,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "SEED_ON_EMPTY": False,
}
```

`tests/conftest.py` (replace the whole file):
```python
import itertools

import pytest

from app import create_app
from app.entity import UserAccount, UserProfile, db
from app.entity.user_profile import DEFAULT_PROFILE_NAMES
from tests.helpers import TEST_CONFIG, TEST_PASSWORD


@pytest.fixture
def app():
    app = create_app(TEST_CONFIG)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def default_profiles(app):
    return {
        role: UserProfile.create(name, role) for role, name in DEFAULT_PROFILE_NAMES.items()
    }


@pytest.fixture
def make_account(default_profiles):
    counter = itertools.count(1)

    def _make(role="customer", password=TEST_PASSWORD, **fields):
        n = next(counter)
        values = {
            "username": f"user{n}",
            "email": f"user{n}@example.com",
            "full_name": f"Test User {n}",
        }
        values.update(fields)
        return UserAccount.create(password=password, profile=default_profiles[role], **values)

    return _make
```

The `app` fixture keeps an app context open for the whole test. Flask reuses that context for test-client requests, so the test and the request share one database session.

- [ ] **Step 3: Write the failing tests**

`tests/unit/__init__.py` and `tests/unit/entity/__init__.py`: empty files.

`tests/unit/entity/test_user_profile.py`:
```python
import pytest

from app.entity import UserProfile


def test_create_profile_persists_fields(app):
    profile = UserProfile.create("Customer", "customer", "Homeowners looking for designers")
    found = UserProfile.find_by_name("Customer")
    assert found.id == profile.id
    assert found.role_type == "customer"
    assert found.description == "Homeowners looking for designers"
    assert found.is_suspended is False


def test_create_profile_rejects_unknown_role(app):
    with pytest.raises(ValueError):
        UserProfile.create("Hacker", "superuser")


def test_find_default_for_role_uses_default_names(default_profiles):
    assert UserProfile.find_default_for_role("designer").name == "Interior Designer"
    assert UserProfile.find_default_for_role("nobody") is None
```

`tests/unit/entity/test_user_account.py`:
```python
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import LoginAttempt, PasswordResetToken, UserAccount, db
from app.entity.db import utcnow


def test_password_is_hashed_not_stored(make_account):
    account = make_account(password="Secret123")
    assert account.password_hash != "Secret123"
    assert account.check_password("Secret123")
    assert not account.check_password("secret123")


def test_email_is_stored_lowercase_and_found_case_insensitively(make_account):
    account = make_account(email="Mixed@Example.COM")
    assert account.email == "mixed@example.com"
    assert UserAccount.find_by_email("MIXED@example.com").id == account.id


def test_role_comes_from_profile(make_account):
    assert make_account(role="designer").role == "designer"


def test_active_account_can_log_in(make_account):
    assert make_account().can_log_in()


def test_suspended_account_cannot_log_in(make_account):
    account = make_account()
    account.is_suspended = True
    assert not account.can_log_in()


def test_account_with_suspended_profile_cannot_log_in(make_account):
    account = make_account()
    account.profile.is_suspended = True
    assert not account.can_log_in()


def test_anonymised_account_cannot_log_in(make_account):
    account = make_account()
    account.is_anonymised = True
    assert not account.can_log_in()


def test_change_password_replaces_hash(make_account):
    account = make_account(password="OldPass123")
    account.change_password("NewPass456")
    db.session.expire_all()
    reloaded = UserAccount.find_by_id(account.id)
    assert reloaded.check_password("NewPass456")
    assert not reloaded.check_password("OldPass123")


def test_username_must_be_unique(make_account):
    make_account(username="alice")
    with pytest.raises(IntegrityError):
        make_account(username="alice")


def test_login_attempt_allows_unknown_username(app):
    attempt = LoginAttempt(username="ghost", account_id=None, success=False)
    db.session.add(attempt)
    db.session.commit()
    assert attempt.attempted_at is not None


def test_reset_token_hash_is_unique(make_account):
    account = make_account()
    expires = utcnow() + timedelta(hours=1)
    db.session.add(PasswordResetToken(account_id=account.id, token_hash="abc", expires_at=expires))
    db.session.commit()
    db.session.add(PasswordResetToken(account_id=account.id, token_hash="abc", expires_at=expires))
    with pytest.raises(IntegrityError):
        db.session.commit()
```

- [ ] **Step 4: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest`
Expected: collection errors, `ModuleNotFoundError: No module named 'app.entity'`

```bash
git add tests
git commit -m "test(entities): user profile and account behaviour"
git push -u origin chore/user-entities
```

The CI run for this push fails. That failure is TDD evidence.

- [ ] **Step 5: Write the entities**

`app/entity/db.py`:
```python
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow() -> datetime:
    """Current UTC time without tzinfo (SQLite stores naive datetimes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

`app/entity/user_profile.py`:
```python
from app.entity.db import db

ROLE_TYPES = ("admin", "designer", "customer", "platform")

DEFAULT_PROFILE_NAMES = {
    "admin": "User Admin",
    "designer": "Interior Designer",
    "customer": "Customer",
    "platform": "Platform Manager",
}


class UserProfile(db.Model):
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    role_type = db.Column(db.String(20), nullable=False)
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)

    accounts = db.relationship("UserAccount", back_populates="profile")

    @classmethod
    def create(cls, name: str, role_type: str, description: str = "") -> "UserProfile":
        if role_type not in ROLE_TYPES:
            raise ValueError(f"Unknown role type: {role_type}")
        profile = cls(name=name, role_type=role_type, description=description)
        db.session.add(profile)
        db.session.commit()
        return profile

    @classmethod
    def find_by_name(cls, name: str) -> "UserProfile | None":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_default_for_role(cls, role_type: str) -> "UserProfile | None":
        name = DEFAULT_PROFILE_NAMES.get(role_type)
        return cls.find_by_name(name) if name else None
```

`app/entity/user_account.py`:
```python
from werkzeug.security import check_password_hash, generate_password_hash

from app.entity.db import db, utcnow


class UserAccount(db.Model):
    __tablename__ = "user_account"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, default="")
    profile_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), nullable=False)
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    is_anonymised = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    profile = db.relationship("UserProfile", back_populates="accounts")

    @property
    def role(self) -> str:
        return self.profile.role_type

    @classmethod
    def create(cls, username, email, password, full_name, profile, phone="") -> "UserAccount":
        account = cls(
            username=username,
            email=email.lower(),
            full_name=full_name,
            phone=phone,
            profile=profile,
        )
        account.set_password(password)
        db.session.add(account)
        db.session.commit()
        return account

    @classmethod
    def find_by_id(cls, account_id: int) -> "UserAccount | None":
        return db.session.get(cls, account_id)

    @classmethod
    def find_by_username(cls, username: str) -> "UserAccount | None":
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email: str) -> "UserAccount | None":
        return cls.query.filter_by(email=email.lower()).first()

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def change_password(self, new_password: str) -> None:
        self.set_password(new_password)
        db.session.commit()

    def can_log_in(self) -> bool:
        return not (self.is_suspended or self.is_anonymised or self.profile.is_suspended)
```

`app/entity/login_attempt.py`:
```python
from app.entity.db import db, utcnow


class LoginAttempt(db.Model):
    __tablename__ = "login_attempt"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
```

`app/entity/password_reset_token.py`:
```python
from app.entity.db import db


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_token"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    token_hash = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
```

`app/entity/__init__.py`:
```python
"""Entity layer. Importing this package registers every table with SQLAlchemy."""

from app.entity.db import db
from app.entity.login_attempt import LoginAttempt
from app.entity.password_reset_token import PasswordResetToken
from app.entity.user_account import UserAccount
from app.entity.user_profile import UserProfile

__all__ = ["LoginAttempt", "PasswordResetToken", "UserAccount", "UserProfile", "db"]
```

`app/__init__.py` (replace the whole file):
```python
import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from app.entity import db

DEV_SECRET_KEY = "dev-only-not-secret"

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, template_folder="boundary/templates")
    app.config.from_mapping(
        SITE_NAME="RenoMatch",
        SECRET_KEY=os.environ.get("SECRET_KEY", DEV_SECRET_KEY),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "renomatch.db")
        ),
    )
    if test_config:
        app.config.update(test_config)
    if os.environ.get("RENDER") and app.config["SECRET_KEY"] == DEV_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production.")

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)

    from app.boundary import register_blueprints

    register_blueprints(app)

    with app.app_context():
        db.create_all()
    return app
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest`
Expected: all tests pass (17).

Run: `ruff check .`
Expected: `All checks passed!`

- [ ] **Step 7: Commit, push (green), merge**

```bash
git add app
git commit -m "feat(entities): user profile, account, login attempt, reset token"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
```

---

### Task 5: Portfolio entities

**Files:**
- Create: `app/entity/company_info.py`, `app/entity/category.py`, `app/entity/idp.py`, `app/entity/idp_photo.py`
- Modify: `app/entity/__init__.py`, `tests/conftest.py`
- Test: `tests/unit/entity/test_portfolio_entities.py`

**Interfaces:**
- Consumes: `db`, `utcnow`, `UserAccount`, and fixtures `app` and `make_account` (Task 4)
- Produces:
  - Models `CompanyInfo` (unique `designer_id`, relationship `designer`), `Category` (unique `name`), `IDP` (relationships `designer`, `category`, and `photos` ordered by `position`), `IDPPhoto` (relationship `idp`)
  - Constants `IDP_STATUSES`, `PROPERTY_TYPES`, `STYLES` in `app.entity.idp`
  - Fixtures `make_category(**fields)` and `make_idp(designer=None, category=None, **fields)`

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b chore/portfolio-entities
```

- [ ] **Step 2: Add the fixtures**

In `tests/conftest.py`, change the entity import line to:
```python
from app.entity import IDP, Category, UserAccount, UserProfile, db
```

Append to the end of `tests/conftest.py`:
```python
@pytest.fixture
def make_category(app):
    counter = itertools.count(1)

    def _make(**fields):
        n = next(counter)
        values = {"name": f"Category {n}", "description": "Test category"}
        values.update(fields)
        category = Category(**values)
        db.session.add(category)
        db.session.commit()
        return category

    return _make


@pytest.fixture
def make_idp(make_account, make_category):
    def _make(designer=None, category=None, **fields):
        values = {
            "title": "Modern HDB living room",
            "style": "Modern",
            "property_type": "HDB",
            "budget": 45000,
            "location": "Tampines",
        }
        values.update(fields)
        idp = IDP(
            designer=designer or make_account(role="designer"),
            category=category or make_category(),
            **values,
        )
        db.session.add(idp)
        db.session.commit()
        return idp

    return _make
```

- [ ] **Step 3: Write the failing tests**

`tests/unit/entity/test_portfolio_entities.py`:
```python
import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import IDP, CompanyInfo, IDPPhoto, db


def test_designer_can_have_only_one_company(make_account):
    designer = make_account(role="designer")
    db.session.add(CompanyInfo(designer=designer, name="Studio One"))
    db.session.commit()
    db.session.add(CompanyInfo(designer=designer, name="Studio Two"))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_category_names_are_unique(make_category):
    make_category(name="Kitchen Remodel")
    with pytest.raises(IntegrityError):
        make_category(name="Kitchen Remodel")


def test_new_idp_defaults_to_current_and_visible(make_idp):
    idp = make_idp()
    assert idp.status == "current"
    assert (idp.is_archived, idp.is_featured, idp.is_removed) == (False, False, False)
    assert idp.created_at is not None


def test_idp_links_designer_and_category(make_account, make_category, make_idp):
    designer = make_account(role="designer")
    category = make_category(name="Kitchen Carpentry")
    idp = make_idp(designer=designer, category=category)
    assert idp.designer.id == designer.id
    assert idp.category.name == "Kitchen Carpentry"


def test_idp_photos_come_back_in_position_order(make_idp):
    idp = make_idp()
    idp.photos.append(IDPPhoto(content_type="image/png", data=b"second", position=2))
    idp.photos.append(IDPPhoto(content_type="image/png", data=b"first", position=1))
    db.session.commit()
    db.session.expire_all()
    assert [p.data for p in db.session.get(IDP, idp.id).photos] == [b"first", b"second"]
```

- [ ] **Step 4: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest`
Expected: `ImportError: cannot import name 'IDP' from 'app.entity'`

```bash
git add tests
git commit -m "test(entities): company, category, IDP and photo rules"
git push -u origin chore/portfolio-entities
```

- [ ] **Step 5: Write the entities**

`app/entity/company_info.py`:
```python
from app.entity.db import db, utcnow


class CompanyInfo(db.Model):
    __tablename__ = "company_info"

    id = db.Column(db.Integer, primary_key=True)
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), unique=True, nullable=False
    )
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    address = db.Column(db.String(255), nullable=False, default="")
    phone = db.Column(db.String(20), nullable=False, default="")
    email = db.Column(db.String(120), nullable=False, default="")
    website = db.Column(db.String(200), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    designer = db.relationship("UserAccount")
```

`app/entity/category.py`:
```python
from app.entity.db import db


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False, default="")
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)
```

`app/entity/idp.py`:
```python
from app.entity.db import db, utcnow

IDP_STATUSES = ("current", "past")
PROPERTY_TYPES = ("HDB", "Condominium", "Landed", "Commercial")
STYLES = (
    "Modern",
    "Scandinavian",
    "Industrial",
    "Minimalist",
    "Contemporary",
    "Japandi",
    "Luxury",
    "Traditional",
    "Eclectic",
    "Mid-Century",
)


class IDP(db.Model):
    """An interior design project in a designer's portfolio."""

    __tablename__ = "idp"

    id = db.Column(db.Integer, primary_key=True)
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    style = db.Column(db.String(30), nullable=False)
    property_type = db.Column(db.String(30), nullable=False)
    budget = db.Column(db.Integer, nullable=False)  # SGD
    location = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="current")
    completed_on = db.Column(db.Date, nullable=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_removed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    designer = db.relationship("UserAccount")
    category = db.relationship("Category")
    photos = db.relationship(
        "IDPPhoto",
        back_populates="idp",
        order_by="IDPPhoto.position",
        cascade="all, delete-orphan",
    )
```

`app/entity/idp_photo.py`:
```python
from app.entity.db import db


class IDPPhoto(db.Model):
    __tablename__ = "idp_photo"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    content_type = db.Column(db.String(50), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    caption = db.Column(db.String(120), nullable=False, default="")
    position = db.Column(db.Integer, nullable=False, default=0)

    idp = db.relationship("IDP", back_populates="photos")
```

`app/entity/__init__.py` (replace the whole file):
```python
"""Entity layer. Importing this package registers every table with SQLAlchemy."""

from app.entity.category import Category
from app.entity.company_info import CompanyInfo
from app.entity.db import db
from app.entity.idp import IDP
from app.entity.idp_photo import IDPPhoto
from app.entity.login_attempt import LoginAttempt
from app.entity.password_reset_token import PasswordResetToken
from app.entity.user_account import UserAccount
from app.entity.user_profile import UserProfile

__all__ = [
    "IDP",
    "Category",
    "CompanyInfo",
    "IDPPhoto",
    "LoginAttempt",
    "PasswordResetToken",
    "UserAccount",
    "UserProfile",
    "db",
]
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest && ruff check .`
Expected: all tests pass; `All checks passed!`

- [ ] **Step 7: Commit, push (green), merge**

```bash
git add app
git commit -m "feat(entities): company info, category, IDP and IDP photo"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
```

---

### Task 6: Engagement, moderation and audit entities

**Files:**
- Create: `app/entity/favourite.py`, `app/entity/view_event.py`, `app/entity/shortlist_event.py`, `app/entity/enquiry.py`, `app/entity/review.py`, `app/entity/idp_flag.py`, `app/entity/audit_log.py`
- Modify: `app/entity/__init__.py`
- Test: `tests/unit/entity/test_engagement_entities.py`

**Interfaces:**
- Consumes: `db`, `utcnow`, `UserAccount`, `IDP`, and fixtures `make_account` and `make_idp`
- Produces:
  - `Favourite` (unique per customer and IDP; relationships `customer`, `idp`)
  - `ViewEvent` (`viewer_id` may be null)
  - `ShortlistEvent`
  - `Enquiry` (relationships `customer`, `designer`, `idp`, and `messages` ordered by `sent_at`) and `EnquiryMessage` (relationships `enquiry`, `sender`)
  - `Review` (rating must be 1–5; relationships `customer`, `designer`)
  - `IDPFlag` (`status` defaults to `"open"`; relationships `idp`, `reporter`, `reviewer`) and `FLAG_STATUSES`
  - `AuditLog` (relationship `actor`)

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b chore/engagement-entities
```

- [ ] **Step 2: Write the failing tests**

`tests/unit/entity/test_engagement_entities.py`:
```python
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.entity import (
    AuditLog,
    Enquiry,
    EnquiryMessage,
    Favourite,
    IDPFlag,
    Review,
    ShortlistEvent,
    ViewEvent,
    db,
)
from app.entity.db import utcnow


def test_customer_can_favourite_an_idp_only_once(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    db.session.add(Favourite(customer=customer, idp=idp, note="Nice kitchen"))
    db.session.commit()
    db.session.add(Favourite(customer=customer, idp=idp))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_view_event_allows_anonymous_visitor(make_idp):
    event = ViewEvent(idp_id=make_idp().id, viewer_id=None)
    db.session.add(event)
    db.session.commit()
    assert event.viewed_at is not None


def test_shortlist_events_accumulate_independently_of_favourites(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    db.session.add_all(
        [ShortlistEvent(idp_id=idp.id, customer_id=customer.id) for _ in range(2)]
    )
    db.session.commit()
    assert db.session.query(ShortlistEvent).filter_by(idp_id=idp.id).count() == 2


@pytest.mark.parametrize("rating", [0, 6])
def test_review_rating_must_be_between_1_and_5(make_account, rating):
    customer, designer = make_account(), make_account(role="designer")
    db.session.add(Review(customer=customer, designer=designer, rating=rating))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_enquiry_messages_are_ordered_by_time(make_account, make_idp):
    customer, idp = make_account(), make_idp()
    enquiry = Enquiry(customer=customer, designer=idp.designer, idp=idp, subject="Price?")
    now = utcnow()
    enquiry.messages.append(
        EnquiryMessage(sender=idp.designer, body="Reply", sent_at=now + timedelta(hours=1))
    )
    enquiry.messages.append(EnquiryMessage(sender=customer, body="Question", sent_at=now))
    db.session.add(enquiry)
    db.session.commit()
    db.session.expire_all()
    assert [m.body for m in db.session.get(Enquiry, enquiry.id).messages] == ["Question", "Reply"]


def test_new_flag_is_open_and_unreviewed(make_account, make_idp):
    flag = IDPFlag(idp=make_idp(), reporter=make_account(), reason="Copied photos")
    db.session.add(flag)
    db.session.commit()
    assert flag.status == "open"
    assert flag.reviewed_by is None
    assert flag.created_at is not None


def test_audit_log_records_actor_and_target(make_account):
    admin, target = make_account(role="admin"), make_account()
    entry = AuditLog(
        actor=admin, action="suspend_account", target_type="user_account", target_id=target.id
    )
    db.session.add(entry)
    db.session.commit()
    assert entry.created_at is not None
    assert entry.actor.role == "admin"
```

- [ ] **Step 3: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest`
Expected: `ImportError: cannot import name 'AuditLog' from 'app.entity'`

```bash
git add tests
git commit -m "test(entities): favourites, events, enquiries, reviews, flags, audit log"
git push -u origin chore/engagement-entities
```

- [ ] **Step 4: Write the entities**

`app/entity/favourite.py`:
```python
from app.entity.db import db, utcnow


class Favourite(db.Model):
    __tablename__ = "favourite"
    __table_args__ = (
        db.UniqueConstraint("customer_id", "idp_id", name="uq_favourite_customer_idp"),
    )

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False)
    note = db.Column(db.String(255), nullable=False, default="")
    saved_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    customer = db.relationship("UserAccount")
    idp = db.relationship("IDP")
```

`app/entity/view_event.py`:
```python
from app.entity.db import db, utcnow


class ViewEvent(db.Model):
    __tablename__ = "view_event"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    viewer_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    viewed_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
```

`app/entity/shortlist_event.py`:
```python
from app.entity.db import db, utcnow


class ShortlistEvent(db.Model):
    """Recorded every time a customer saves an IDP. Never deleted."""

    __tablename__ = "shortlist_event"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    shortlisted_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
```

`app/entity/enquiry.py`:
```python
from app.entity.db import db, utcnow


class Enquiry(db.Model):
    __tablename__ = "enquiry"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=True)
    subject = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    customer = db.relationship("UserAccount", foreign_keys=[customer_id])
    designer = db.relationship("UserAccount", foreign_keys=[designer_id])
    idp = db.relationship("IDP")
    messages = db.relationship(
        "EnquiryMessage",
        back_populates="enquiry",
        order_by="EnquiryMessage.sent_at",
        cascade="all, delete-orphan",
    )


class EnquiryMessage(db.Model):
    __tablename__ = "enquiry_message"

    id = db.Column(db.Integer, primary_key=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey("enquiry.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    enquiry = db.relationship("Enquiry", back_populates="messages")
    sender = db.relationship("UserAccount")
```

`app/entity/review.py`:
```python
from app.entity.db import db, utcnow


class Review(db.Model):
    __tablename__ = "review"
    __table_args__ = (db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),)

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    customer = db.relationship("UserAccount", foreign_keys=[customer_id])
    designer = db.relationship("UserAccount", foreign_keys=[designer_id])
```

`app/entity/idp_flag.py`:
```python
from app.entity.db import db, utcnow

FLAG_STATUSES = ("open", "upheld", "dismissed")


class IDPFlag(db.Model):
    """A user's report that an IDP is inappropriate."""

    __tablename__ = "idp_flag"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="open")
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    idp = db.relationship("IDP")
    reporter = db.relationship("UserAccount", foreign_keys=[reporter_id])
    reviewer = db.relationship("UserAccount", foreign_keys=[reviewed_by])
```

`app/entity/audit_log.py`:
```python
from app.entity.db import db, utcnow


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(30), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    details = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    actor = db.relationship("UserAccount")
```

`app/entity/__init__.py` (replace the whole file):
```python
"""Entity layer. Importing this package registers every table with SQLAlchemy."""

from app.entity.audit_log import AuditLog
from app.entity.category import Category
from app.entity.company_info import CompanyInfo
from app.entity.db import db
from app.entity.enquiry import Enquiry, EnquiryMessage
from app.entity.favourite import Favourite
from app.entity.idp import IDP
from app.entity.idp_flag import IDPFlag
from app.entity.idp_photo import IDPPhoto
from app.entity.login_attempt import LoginAttempt
from app.entity.password_reset_token import PasswordResetToken
from app.entity.review import Review
from app.entity.shortlist_event import ShortlistEvent
from app.entity.user_account import UserAccount
from app.entity.user_profile import UserProfile
from app.entity.view_event import ViewEvent

__all__ = [
    "IDP",
    "AuditLog",
    "Category",
    "CompanyInfo",
    "Enquiry",
    "EnquiryMessage",
    "Favourite",
    "IDPFlag",
    "IDPPhoto",
    "LoginAttempt",
    "PasswordResetToken",
    "Review",
    "ShortlistEvent",
    "UserAccount",
    "UserProfile",
    "ViewEvent",
    "db",
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest && ruff check .`
Expected: all tests pass; `All checks passed!`

- [ ] **Step 6: Commit, push (green), merge**

```bash
git add app
git commit -m "feat(entities): favourites, events, enquiries, reviews, flags, audit log"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
```

---

### Task 7: Test data generator and seed on startup

**Files:**
- Create: `app/seed.py`
- Modify: `app/__init__.py`, `README.md`
- Test: `tests/unit/test_seed.py`, `tests/unit/test_seed_guard.py`

**Interfaces:**
- Consumes: every entity from Tasks 4–6; `DEFAULT_PROFILE_NAMES`; `STYLES` and `PROPERTY_TYPES`
- Produces:
  - `seed_database(seed: int = 314) -> dict[str, int]`, which returns a row count per table and raises `RuntimeError` if any account already exists
  - `register_seed_command(app)`, which adds `flask seed [--reset]`
  - Constants `SEED_PASSWORD = "Password123!"` and `DEMO_USERNAMES = {"admin": "admin", "platform": "manager", "designer": "designer", "customer": "customer"}`
  - Config key `SEED_ON_EMPTY` (env `SEED_ON_EMPTY`, default `"1"`)

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b chore/seed-data
```

- [ ] **Step 2: Write the failing tests**

`tests/unit/test_seed.py`:
```python
import pytest

from app import create_app
from app.entity import (
    IDP,
    AuditLog,
    Category,
    CompanyInfo,
    Enquiry,
    EnquiryMessage,
    Favourite,
    IDPFlag,
    IDPPhoto,
    LoginAttempt,
    Review,
    ShortlistEvent,
    UserAccount,
    UserProfile,
    ViewEvent,
    db,
)
from app.seed import DEMO_USERNAMES, SEED_PASSWORD, seed_database
from tests.helpers import TEST_CONFIG

MAIN_ENTITIES = [
    UserProfile,
    UserAccount,
    LoginAttempt,
    CompanyInfo,
    Category,
    IDP,
    IDPPhoto,
    Favourite,
    Enquiry,
    EnquiryMessage,
    Review,
    IDPFlag,
    AuditLog,
]


@pytest.fixture(scope="module")
def seeded():
    app = create_app(TEST_CONFIG)
    with app.app_context():
        seed_database()
        yield
        db.session.remove()
        db.drop_all()


@pytest.mark.parametrize("entity", MAIN_ENTITIES, ids=lambda e: e.__name__)
def test_at_least_100_rows_per_main_entity(seeded, entity):
    assert db.session.query(entity).count() >= 100


def test_events_are_plentiful_and_span_the_last_90_days(seeded):
    assert db.session.query(ViewEvent).count() >= 5000
    assert db.session.query(ShortlistEvent).count() > db.session.query(Favourite).count()
    oldest = db.session.query(db.func.min(ViewEvent.viewed_at)).scalar()
    newest = db.session.query(db.func.max(ViewEvent.viewed_at)).scalar()
    assert (newest - oldest).days >= 80


def test_demo_accounts_log_in_with_seed_password(seeded):
    for role, username in DEMO_USERNAMES.items():
        account = UserAccount.find_by_username(username)
        assert account.role == role
        assert account.check_password(SEED_PASSWORD)
        assert account.can_log_in()


def test_every_review_follows_a_designer_reply(seeded):
    for review in db.session.query(Review):
        reply = (
            db.session.query(EnquiryMessage)
            .join(Enquiry)
            .filter(
                Enquiry.customer_id == review.customer_id,
                Enquiry.designer_id == review.designer_id,
                EnquiryMessage.sender_id == review.designer_id,
            )
            .first()
        )
        assert reply is not None
```

`tests/unit/test_seed_guard.py`:
```python
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
```

- [ ] **Step 3: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest tests/unit/test_seed.py tests/unit/test_seed_guard.py`
Expected: `ModuleNotFoundError: No module named 'app.seed'`

```bash
git add tests
git commit -m "test(seed): 100+ rows per entity, demo accounts, review rule"
git push -u origin chore/seed-data
```

- [ ] **Step 4: Write the generator**

`app/seed.py`:
```python
"""Generated test data: 100+ rows per main entity, events over the last 90 days."""

import random
from datetime import timedelta
from html import escape

import click
from faker import Faker
from werkzeug.security import generate_password_hash

from app.entity import (
    IDP,
    AuditLog,
    Category,
    CompanyInfo,
    Enquiry,
    EnquiryMessage,
    Favourite,
    IDPFlag,
    IDPPhoto,
    LoginAttempt,
    Review,
    ShortlistEvent,
    UserAccount,
    UserProfile,
    ViewEvent,
    db,
)
from app.entity.db import utcnow
from app.entity.idp import PROPERTY_TYPES, STYLES
from app.entity.user_profile import DEFAULT_PROFILE_NAMES

SEED_PASSWORD = "Password123!"
DEMO_USERNAMES = {
    "admin": "admin",
    "platform": "manager",
    "designer": "designer",
    "customer": "customer",
}
ACCOUNT_COUNTS = {"admin": 5, "platform": 5, "designer": 120, "customer": 300}
DESIGNERS_WITHOUT_COMPANY = 10
IDP_COUNT = 400
FAVOURITE_COUNT = 1200
REMOVED_FAVOURITE_COUNT = 300
VIEW_EVENT_COUNT = 8000
ENQUIRY_COUNT = 250
REVIEW_COUNT = 120
FLAG_COUNT = 120
AUDIT_LOG_COUNT = 200
LOGIN_ATTEMPT_COUNT = 500
DAYS_OF_HISTORY = 90

PROFILE_TIERS = [
    "Trial", "Standard", "Premium", "Enterprise", "Senior", "Junior", "Associate", "Lead",
    "Regional North", "Regional South", "Regional East", "Regional West", "Central",
    "Corporate", "Student", "Partner", "Verified", "Featured", "Legacy", "Pilot", "Seasonal",
    "VIP", "Support", "Contract",
]
ROOMS = [
    "Living Room", "Kitchen", "Bedroom", "Bathroom", "Study", "Dining Room", "Balcony",
    "Whole Unit", "Office", "Retail",
]
THEMES = [
    "Full Renovation", "Refresh", "Remodel", "Storage Solutions", "Lighting", "Carpentry",
    "Flooring", "Smart Home", "Eco-Friendly", "Space Saving",
]
LOCATIONS = [
    "Ang Mo Kio", "Bedok", "Bishan", "Bukit Batok", "Bukit Merah", "Bukit Timah", "Clementi",
    "Hougang", "Jurong East", "Jurong West", "Kallang", "Marine Parade", "Pasir Ris",
    "Punggol", "Queenstown", "Sengkang", "Serangoon", "Tampines", "Toa Payoh", "Woodlands",
    "Yishun", "Novena", "Orchard", "Tiong Bahru",
]
COMPANY_SUFFIXES = ["Interiors", "Design Studio", "Living", "Spaces"]
FAVOURITE_NOTES = [
    "Love the kitchen layout", "Similar size to our flat", "Check budget with designer",
    "Good storage ideas", "Show to my partner", "Like the colour palette",
]
FLAG_REASONS = [
    "Photos appear to be copied from another designer",
    "Contains contact details in the description",
    "Inappropriate image",
    "Misleading budget information",
    "Duplicate listing",
]
AUDIT_ACTIONS = [
    "create_account", "update_account", "suspend_account", "reactivate_account",
    "create_profile", "update_profile", "suspend_profile", "reactivate_profile",
]
PHOTO_COLOURS = [
    "#8d6e63", "#a1887f", "#90a4ae", "#b0bec5", "#c5e1a5",
    "#ffe082", "#ffab91", "#80cbc4", "#ce93d8", "#9fa8da",
]

ALL_MODELS = [
    UserProfile, UserAccount, LoginAttempt, CompanyInfo, Category, IDP, IDPPhoto, Favourite,
    ShortlistEvent, ViewEvent, Enquiry, EnquiryMessage, Review, IDPFlag, AuditLog,
]


def seed_database(seed: int = 314) -> dict[str, int]:
    """Fill an empty database with generated data and return a row count per table."""
    if db.session.query(UserAccount).first() is not None:
        raise RuntimeError("Database already has accounts; refusing to seed.")
    _Seeder(seed).run()
    return {model.__tablename__: db.session.query(model).count() for model in ALL_MODELS}


def register_seed_command(app) -> None:
    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Drop and recreate all tables first.")
    def seed_command(reset):
        """Fill the database with generated test data."""
        if reset:
            db.drop_all()
            db.create_all()
        for table, count in seed_database().items():
            click.echo(f"{table}: {count}")


def _placeholder_svg(colour: str, label: str) -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">'
        f'<rect width="800" height="600" fill="{colour}"/>'
        '<text x="400" y="310" font-family="sans-serif" font-size="40" fill="#ffffff" '
        f'text-anchor="middle">{escape(label)}</text></svg>'
    ).encode()


class _Seeder:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.fake = Faker()
        self.fake.seed_instance(seed)
        self.now = utcnow()

    def past(self, days_max: int = DAYS_OF_HISTORY):
        """A timestamp within the last days_max days, weighted toward recent days."""
        return self.now - timedelta(days=self.rng.triangular(0, days_max, 0))

    def run(self) -> None:
        profiles = self.profiles()
        accounts = self.accounts(profiles)
        designers, customers = accounts["designer"], accounts["customer"]
        self.companies(designers)
        idps = self.idps(designers, self.categories())
        self.photos(idps)
        visible = [idp for idp in idps if not idp.is_archived]
        self.favourites_and_shortlists(customers, visible)
        self.views(customers, visible)
        self.reviews(self.enquiries(customers, designers, idps))
        self.flags(customers, idps, accounts["platform"])
        self.audit_logs(accounts["admin"], designers + customers)
        self.login_attempts(designers + customers)
        db.session.commit()

    def profiles(self) -> dict[str, list[UserProfile]]:
        by_role = {
            role: [UserProfile(name=name, role_type=role, description=f"Default {name} profile")]
            for role, name in DEFAULT_PROFILE_NAMES.items()
        }
        for i, tier in enumerate(PROFILE_TIERS):
            for role, label in DEFAULT_PROFILE_NAMES.items():
                by_role[role].append(
                    UserProfile(
                        name=f"{tier} {label}",
                        role_type=role,
                        description=f"{tier} tier of {label} accounts",
                        is_suspended=(i % 10 == 9),
                    )
                )
        db.session.add_all(p for group in by_role.values() for p in group)
        db.session.flush()
        return by_role

    def accounts(self, profiles) -> dict[str, list[UserAccount]]:
        password_hash = generate_password_hash(SEED_PASSWORD)
        by_role, n = {}, 0
        for role, count in ACCOUNT_COUNTS.items():
            created = []
            for i in range(count):
                n += 1
                if i == 0:
                    username, profile = DEMO_USERNAMES[role], profiles[role][0]
                else:
                    base = "".join(c for c in self.fake.user_name() if c.isalnum() or c == "_")
                    username = f"{base[:20]}{n}"  # matches the US03 username rule
                    if self.rng.random() < 0.8:
                        profile = profiles[role][0]
                    else:
                        profile = self.rng.choice(profiles[role][1:])
                created.append(
                    UserAccount(
                        username=username,
                        email=f"{username}@example.com",
                        password_hash=password_hash,
                        full_name=self.fake.name(),
                        phone=f"+65 {self.rng.randint(8000, 9999)} {self.rng.randint(1000, 9999)}",
                        profile=profile,
                        is_suspended=(i > 0 and i % 25 == 0),
                        created_at=self.past(DAYS_OF_HISTORY * 2),
                    )
                )
            by_role[role] = created
        db.session.add_all(a for group in by_role.values() for a in group)
        db.session.flush()
        return by_role

    def companies(self, designers) -> None:
        for designer in designers[:-DESIGNERS_WITHOUT_COMPANY]:
            db.session.add(
                CompanyInfo(
                    designer=designer,
                    name=f"{self.fake.last_name()} {self.rng.choice(COMPANY_SUFFIXES)}",
                    description=self.fake.paragraph(nb_sentences=4),
                    address=(
                        f"{self.rng.randint(1, 999)} {self.rng.choice(LOCATIONS)} Road, "
                        f"Singapore {self.rng.randint(100000, 829999)}"
                    ),
                    phone=designer.phone,
                    email=f"hello@{designer.username}.example.com",
                    website=f"https://{designer.username}.example.com",
                )
            )

    def categories(self) -> list[Category]:
        categories = [
            Category(
                name=f"{room} {theme}",
                description=f"{theme} projects for the {room.lower()}",
                is_suspended=(i % 20 == 19),
            )
            for i, (room, theme) in enumerate((r, t) for r in ROOMS for t in THEMES)
        ]
        db.session.add_all(categories)
        db.session.flush()
        return categories

    def idps(self, designers, categories) -> list[IDP]:
        active = [c for c in categories if not c.is_suspended]
        idps = []
        for i in range(IDP_COUNT):
            style = self.rng.choice(STYLES)
            location = self.rng.choice(LOCATIONS)
            category = self.rng.choice(active)
            is_past = self.rng.random() < 0.7
            completed_on = None
            if is_past:
                completed_on = (self.now - timedelta(days=self.rng.randint(30, 1500))).date()
            idps.append(
                IDP(
                    designer=designers[i % len(designers)],
                    category=category,
                    title=f"{style} {category.name} in {location}"[:120],
                    description=self.fake.paragraph(nb_sentences=5),
                    style=style,
                    property_type=self.rng.choice(PROPERTY_TYPES),
                    budget=self.rng.randrange(15_000, 250_001, 1_000),
                    location=location,
                    status="past" if is_past else "current",
                    completed_on=completed_on,
                    is_featured=(i % 40 == 0),
                    is_archived=(i % 80 == 79),
                    created_at=self.past(DAYS_OF_HISTORY * 2),
                )
            )
        db.session.add_all(idps)
        db.session.flush()
        return idps

    def photos(self, idps) -> None:
        for idp in idps:
            for position in range(self.rng.randint(1, 3)):
                db.session.add(
                    IDPPhoto(
                        idp=idp,
                        content_type="image/svg+xml",
                        data=_placeholder_svg(
                            self.rng.choice(PHOTO_COLOURS), f"{idp.style} #{position + 1}"
                        ),
                        caption=f"{idp.style} {idp.property_type}, view {position + 1}",
                        position=position,
                    )
                )

    def favourites_and_shortlists(self, customers, visible) -> None:
        pairs = set()
        while len(pairs) < FAVOURITE_COUNT + REMOVED_FAVOURITE_COUNT:
            pairs.add((self.rng.randrange(len(customers)), self.rng.randrange(len(visible))))
        ordered = sorted(pairs)
        self.rng.shuffle(ordered)
        for n, (c, i) in enumerate(ordered):
            customer, idp = customers[c], visible[i]
            saved_at = self.past()
            db.session.add(
                ShortlistEvent(idp_id=idp.id, customer_id=customer.id, shortlisted_at=saved_at)
            )
            if n < FAVOURITE_COUNT:  # the rest were saved and later removed
                note = self.rng.choice(FAVOURITE_NOTES) if self.rng.random() < 0.4 else ""
                db.session.add(
                    Favourite(customer=customer, idp=idp, note=note, saved_at=saved_at)
                )

    def views(self, customers, visible) -> None:
        weights = [self.rng.paretovariate(1.5) for _ in visible]  # a few IDPs are far more popular
        for idp in self.rng.choices(visible, weights=weights, k=VIEW_EVENT_COUNT):
            viewer_id = None if self.rng.random() < 0.3 else self.rng.choice(customers).id
            db.session.add(ViewEvent(idp_id=idp.id, viewer_id=viewer_id, viewed_at=self.past()))

    def enquiries(self, customers, designers, idps) -> list[tuple[UserAccount, UserAccount]]:
        idps_by_designer = {}
        for idp in idps:
            idps_by_designer.setdefault(idp.designer_id, []).append(idp)
        replied = []
        for i in range(ENQUIRY_COUNT):
            customer = customers[i % len(customers)]
            designer = designers[(i * 7) % len(designers)]
            idp = self.rng.choice(idps_by_designer[designer.id])
            created = self.past()
            enquiry = Enquiry(
                customer_id=customer.id,
                designer_id=designer.id,
                idp_id=idp.id,
                subject=f"Enquiry about {idp.title}",
                created_at=created,
            )
            enquiry.messages.append(
                EnquiryMessage(
                    sender_id=customer.id,
                    body=self.fake.paragraph(nb_sentences=3),
                    sent_at=created,
                )
            )
            if i % 5 != 0:  # four in five enquiries get a reply
                enquiry.messages.append(
                    EnquiryMessage(
                        sender_id=designer.id,
                        body=self.fake.paragraph(nb_sentences=3),
                        sent_at=min(created + timedelta(hours=self.rng.randint(1, 48)), self.now),
                    )
                )
                replied.append((customer, designer))
            db.session.add(enquiry)
        return replied

    def reviews(self, replied_pairs) -> None:
        for customer, designer in replied_pairs[:REVIEW_COUNT]:
            db.session.add(
                Review(
                    customer_id=customer.id,
                    designer_id=designer.id,
                    rating=self.rng.choices([1, 2, 3, 4, 5], weights=[1, 1, 3, 6, 8])[0],
                    comment=self.fake.paragraph(nb_sentences=2),
                )
            )

    def flags(self, customers, idps, managers) -> None:
        statuses = ["open", "open", "dismissed", "upheld"]
        for i in range(FLAG_COUNT):
            idp = idps[(i * 3) % len(idps)]
            status = statuses[i % len(statuses)]
            flag = IDPFlag(
                idp_id=idp.id,
                reporter_id=self.rng.choice(customers).id,
                reason=self.rng.choice(FLAG_REASONS),
                status=status,
                created_at=self.past(),
            )
            if status != "open":
                flag.reviewed_by = self.rng.choice(managers).id
                flag.reviewed_at = self.now
                if status == "upheld":
                    idp.is_removed = True
            db.session.add(flag)

    def audit_logs(self, admins, targets) -> None:
        for _ in range(AUDIT_LOG_COUNT):
            target = self.rng.choice(targets)
            action = self.rng.choice(AUDIT_ACTIONS)
            is_profile = "profile" in action
            db.session.add(
                AuditLog(
                    actor_id=self.rng.choice(admins).id,
                    action=action,
                    target_type="user_profile" if is_profile else "user_account",
                    target_id=target.profile_id if is_profile else target.id,
                    details=f"{action.replace('_', ' ')} via admin console",
                    created_at=self.past(),
                )
            )

    def login_attempts(self, accounts) -> None:
        for _ in range(LOGIN_ATTEMPT_COUNT):
            account = self.rng.choice(accounts)
            db.session.add(
                LoginAttempt(
                    username=account.username,
                    account_id=account.id,
                    success=self.rng.random() < 0.85,
                    attempted_at=self.past(),
                )
            )
```

- [ ] **Step 5: Seed on startup in the app factory**

`app/__init__.py` (replace the whole file):
```python
import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from app.entity import UserAccount, db

DEV_SECRET_KEY = "dev-only-not-secret"

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, template_folder="boundary/templates")
    app.config.from_mapping(
        SITE_NAME="RenoMatch",
        SECRET_KEY=os.environ.get("SECRET_KEY", DEV_SECRET_KEY),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "renomatch.db")
        ),
        SEED_ON_EMPTY=os.environ.get("SEED_ON_EMPTY", "1") == "1",
    )
    if test_config:
        app.config.update(test_config)
    if os.environ.get("RENDER") and app.config["SECRET_KEY"] == DEV_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production.")

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)

    from app.boundary import register_blueprints
    from app.seed import register_seed_command, seed_database

    register_blueprints(app)
    register_seed_command(app)

    with app.app_context():
        db.create_all()
        if app.config["SEED_ON_EMPTY"] and db.session.query(UserAccount).first() is None:
            seed_database()
    return app
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest && ruff check .`
Expected: all tests pass; `All checks passed!` The seed tests take a few seconds.

Then check the real database by hand:
```bash
flask --app app seed --reset
```
Expected: one `table: count` line per table, each main table at 100 or more.

- [ ] **Step 7: Document the demo accounts**

Append to `README.md`:
```markdown
## Test data and demo accounts

On startup the app fills an empty database with generated data: 100+ rows per main entity,
plus about 8,000 views and 1,500 shortlists spread over the last 90 days.
To rebuild it locally: `flask --app app seed --reset`.

Every seeded account's password is `Password123!`.

| Role | Username |
|---|---|
| User Admin | `admin` |
| Platform Manager | `manager` |
| Interior Designer | `designer` |
| Customer | `customer` |
```

- [ ] **Step 8: Commit, push (green), merge**

```bash
git add app README.md
git commit -m "feat(seed): generate 100+ rows per entity and seed empty databases on startup"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
```

After the deploy job finishes, check the live site's logs in the Render dashboard. Startup should complete without errors.

---

### Task 8: US01 Log in

**Files:**
- Create: `app/control/__init__.py`, `app/control/errors.py`, `app/control/login_controller.py`
- Create: `app/boundary/auth_guard.py`, `app/boundary/auth.py`
- Create: `app/boundary/admin.py`, `app/boundary/designer.py`, `app/boundary/customer.py`, `app/boundary/platform.py`
- Create: `app/boundary/templates/auth/login.html`, `app/boundary/templates/role_home.html`
- Modify: `app/boundary/__init__.py`, `app/boundary/templates/_nav.html`, `tests/conftest.py`
- Create: `tests/unit/control/__init__.py`
- Test: `tests/unit/control/test_login_controller.py`, `tests/boundary/test_login_page.py`

**Interfaces:**
- Consumes: `UserAccount.find_by_username`, `find_by_id`, `check_password`, `can_log_in`, `role`
- Produces:
  - `LoginError(Exception)` and `ValidationError(errors: dict[str, str])` with an `.errors` attribute, in `app.control.errors`
  - `LoginController.login(username, password) -> UserAccount` (raises `LoginError`) and `LoginController.get_active_account(account_id) -> UserAccount | None`
  - `ROLE_HOME: dict[str, str]`, mapping each role to its home endpoint; `role_required(*roles)`; `login_required`; `load_current_account()`
  - Endpoints `auth.login` (`/login`), `admin.home` (`/admin/`), `designer.home` (`/designer/`), `customer.home` (`/customer/`), `platform.home` (`/platform/`)
  - Template global `ROLE_HOME`; `g.current_account` on every request
  - Fixture `login(username, password=TEST_PASSWORD)`, which returns the POST response

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b feature/US01-login
```

- [ ] **Step 2: Add the `login` fixture**

Append to `tests/conftest.py`:
```python
@pytest.fixture
def login(client):
    def _login(username, password=TEST_PASSWORD):
        return client.post("/login", data={"username": username, "password": password})

    return _login
```

- [ ] **Step 3: Write the failing tests**

`tests/unit/control/__init__.py`: an empty file.

`tests/unit/control/test_login_controller.py`:
```python
import pytest

from app.control.errors import LoginError
from app.control.login_controller import LoginController
from app.entity import db
from tests.helpers import TEST_PASSWORD


def test_login_returns_account_for_correct_credentials(make_account):
    account = make_account(username="alice")
    assert LoginController().login("alice", TEST_PASSWORD).id == account.id


def test_login_rejects_wrong_password(make_account):
    make_account(username="alice")
    with pytest.raises(LoginError, match="Invalid username or password"):
        LoginController().login("alice", "wrong-password")


def test_login_rejects_unknown_username(default_profiles):
    with pytest.raises(LoginError, match="Invalid username or password"):
        LoginController().login("ghost", TEST_PASSWORD)


def test_login_rejects_suspended_account(make_account):
    account = make_account(username="alice")
    account.is_suspended = True
    db.session.commit()
    with pytest.raises(LoginError, match="suspended"):
        LoginController().login("alice", TEST_PASSWORD)


def test_login_rejects_account_whose_profile_is_suspended(make_account):
    account = make_account(username="alice")
    account.profile.is_suspended = True
    db.session.commit()
    with pytest.raises(LoginError, match="suspended"):
        LoginController().login("alice", TEST_PASSWORD)


def test_get_active_account_only_returns_accounts_that_may_log_in(make_account):
    account = make_account()
    controller = LoginController()
    assert controller.get_active_account(account.id).id == account.id
    account.is_suspended = True
    db.session.commit()
    assert controller.get_active_account(account.id) is None
    assert controller.get_active_account(99999) is None
```

`tests/boundary/test_login_page.py`:
```python
import pytest

from app.entity import db
from tests.helpers import TEST_PASSWORD


@pytest.mark.parametrize(
    "role, home",
    [
        ("admin", "/admin/"),
        ("designer", "/designer/"),
        ("customer", "/customer/"),
        ("platform", "/platform/"),
    ],
)
def test_login_redirects_each_role_to_its_home(client, make_account, role, home):
    account = make_account(role=role)
    resp = client.post("/login", data={"username": account.username, "password": TEST_PASSWORD})
    assert resp.status_code == 302
    assert resp.headers["Location"] == home


def test_login_page_shows_error_for_bad_password(client, make_account):
    account = make_account()
    resp = client.post("/login", data={"username": account.username, "password": "nope"})
    assert resp.status_code == 200
    assert b"Invalid username or password." in resp.data


def test_role_home_requires_login(client, default_profiles):
    resp = client.get("/customer/")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/login"


def test_role_home_forbids_other_roles(client, make_account, login):
    login(make_account(role="customer").username)
    assert client.get("/admin/").status_code == 403


def test_account_suspended_mid_session_is_sent_to_login(client, make_account, login):
    account = make_account(role="customer")
    login(account.username)
    account.is_suspended = True
    db.session.commit()
    assert client.get("/customer/").headers["Location"] == "/login"


def test_logged_in_user_visiting_login_goes_home(client, make_account, login):
    login(make_account(role="platform").username)
    assert client.get("/login").headers["Location"] == "/platform/"


def test_role_home_greets_user_by_name(client, make_account, login):
    login(make_account(role="designer", full_name="Dana Tan").username)
    assert b"Dana Tan" in client.get("/designer/").data
```

- [ ] **Step 4: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest`
Expected: `ModuleNotFoundError: No module named 'app.control'`, and 404 failures for the boundary tests.

```bash
git add tests
git commit -m "test(US01): log in and role-based access"
git push -u origin feature/US01-login
```

- [ ] **Step 5: Write the control layer**

`app/control/__init__.py`: an empty file.

`app/control/errors.py`:
```python
class LoginError(Exception):
    """Credentials are wrong or the account is not allowed to log in."""


class ValidationError(Exception):
    """One or more form fields are invalid. `errors` maps field name to message."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(errors.values()))
        self.errors = errors
```

`app/control/login_controller.py`:
```python
from app.control.errors import LoginError
from app.entity import UserAccount


class LoginController:
    """US01: log in with username and password."""

    def login(self, username: str, password: str) -> UserAccount:
        account = UserAccount.find_by_username(username)
        if account is None or not account.check_password(password):
            raise LoginError("Invalid username or password.")
        if not account.can_log_in():
            raise LoginError("This account is suspended. Please contact an administrator.")
        return account

    def get_active_account(self, account_id: int) -> UserAccount | None:
        account = UserAccount.find_by_id(account_id)
        if account is None or not account.can_log_in():
            return None
        return account
```

- [ ] **Step 6: Write the boundary layer**

`app/boundary/auth_guard.py`:
```python
from functools import wraps

from flask import abort, g, redirect, session, url_for

from app.control.login_controller import LoginController

ROLE_HOME = {
    "admin": "admin.home",
    "designer": "designer.home",
    "customer": "customer.home",
    "platform": "platform.home",
}


def load_current_account() -> None:
    """Before every request: set g.current_account, dropping sessions that are no longer valid."""
    g.current_account = None
    account_id = session.get("account_id")
    if account_id is None:
        return
    account = LoginController().get_active_account(account_id)
    if account is None:
        session.clear()
        return
    g.current_account = account


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            account = g.get("current_account")
            if account is None:
                return redirect(url_for("auth.login"))
            if account.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


login_required = role_required(*ROLE_HOME)
```

`app/boundary/auth.py`:
```python
from flask import Blueprint, g, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import ROLE_HOME, load_current_account
from app.control.errors import LoginError
from app.control.login_controller import LoginController

bp = Blueprint("auth", __name__)
bp.before_app_request(load_current_account)


@bp.app_context_processor
def inject_role_home():
    return {"ROLE_HOME": ROLE_HOME}


class LoginPage(MethodView):
    """Boundary for US01: log in."""

    def get(self):
        if g.current_account is not None:
            return redirect(url_for(ROLE_HOME[g.current_account.role]))
        return render_template("auth/login.html")

    def post(self):
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            account = LoginController().login(username, password)
        except LoginError as error:
            return render_template("auth/login.html", error=str(error), username=username)
        session.clear()
        session["account_id"] = account.id
        return redirect(url_for(ROLE_HOME[account.role]))


bp.add_url_rule("/login", view_func=LoginPage.as_view("login"))
```

`app/boundary/admin.py`:
```python
from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


class AdminHomePage(MethodView):
    decorators = [role_required("admin")]

    def get(self):
        return render_template("role_home.html", role_label="User Admin")


bp.add_url_rule("/", view_func=AdminHomePage.as_view("home"))
```

`app/boundary/designer.py`:
```python
from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("designer", __name__, url_prefix="/designer")


class DesignerHomePage(MethodView):
    decorators = [role_required("designer")]

    def get(self):
        return render_template("role_home.html", role_label="Interior Designer")


bp.add_url_rule("/", view_func=DesignerHomePage.as_view("home"))
```

`app/boundary/customer.py`:
```python
from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("customer", __name__, url_prefix="/customer")


class CustomerHomePage(MethodView):
    decorators = [role_required("customer")]

    def get(self):
        return render_template("role_home.html", role_label="Customer")


bp.add_url_rule("/", view_func=CustomerHomePage.as_view("home"))
```

`app/boundary/platform.py`:
```python
from flask import Blueprint, render_template
from flask.views import MethodView

from app.boundary.auth_guard import role_required

bp = Blueprint("platform", __name__, url_prefix="/platform")


class PlatformHomePage(MethodView):
    decorators = [role_required("platform")]

    def get(self):
        return render_template("role_home.html", role_label="Platform Management")


bp.add_url_rule("/", view_func=PlatformHomePage.as_view("home"))
```

`app/boundary/__init__.py` (replace the whole file):
```python
def register_blueprints(app):
    from app.boundary import admin, auth, customer, designer, platform, public

    for module in (public, auth, admin, designer, customer, platform):
        app.register_blueprint(module.bp)
```

`app/boundary/templates/auth/login.html`:
```html
{% extends "base.html" %}
{% block title %}Log in · {{ config.SITE_NAME }}{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-5">
    <h1 class="h3 mb-3">Log in</h1>
    {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="mb-3">
        <label class="form-label" for="username">Username</label>
        <input class="form-control" id="username" name="username" value="{{ username or '' }}" required autofocus>
      </div>
      <div class="mb-3">
        <label class="form-label" for="password">Password</label>
        <input class="form-control" id="password" name="password" type="password" required>
      </div>
      <button class="btn btn-primary w-100" type="submit">Log in</button>
    </form>
  </div>
</div>
{% endblock %}
```

`app/boundary/templates/role_home.html`:
```html
{% extends "base.html" %}
{% block title %}{{ role_label }} · {{ config.SITE_NAME }}{% endblock %}
{% block content %}
<h1 class="h3">{{ role_label }} home</h1>
<p>Welcome, {{ g.current_account.full_name }}.</p>
<p class="text-body-secondary">Features for this role are added sprint by sprint.</p>
{% endblock %}
```

`app/boundary/templates/_nav.html` (replace the whole file):
```html
{% if g.current_account %}
  <span class="navbar-text me-3">{{ g.current_account.full_name }}</span>
  <a class="nav-link" href="{{ url_for(ROLE_HOME[g.current_account.role]) }}">Home</a>
{% else %}
  <a class="nav-link" href="{{ url_for('auth.login') }}">Log in</a>
{% endif %}
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `python -m pytest && ruff check .`
Expected: all tests pass; `All checks passed!`

Manual check: `flask --app app run --debug`. Log in as `admin` / `Password123!` and confirm you land on "User Admin home". Visiting `/customer/` must return 403.

- [ ] **Step 8: Commit, push (green), merge**

```bash
git add app tests/conftest.py
git commit -m "feat(US01): log in with role-based home pages"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
```

---

### Task 9: US02 Log out

**Files:**
- Create: `app/control/logout_controller.py`
- Modify: `app/boundary/auth.py`, `app/boundary/templates/_nav.html`
- Test: `tests/unit/control/test_logout_controller.py`, `tests/boundary/test_logout.py`

**Interfaces:**
- Consumes: `bp`, `ROLE_HOME` and `load_current_account` from Task 8
- Produces: `LogoutController.logout(session: MutableMapping) -> None`; endpoint `auth.logout` (`POST /logout`)

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b feature/US02-logout
```

- [ ] **Step 2: Write the failing tests**

`tests/unit/control/test_logout_controller.py`:
```python
from app.control.logout_controller import LogoutController


def test_logout_clears_everything_in_the_session():
    session = {"account_id": 5, "theme": "dark"}
    LogoutController().logout(session)
    assert session == {}
```

`tests/boundary/test_logout.py`:
```python
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
```

- [ ] **Step 3: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest tests/unit/control/test_logout_controller.py tests/boundary/test_logout.py`
Expected: `ModuleNotFoundError: No module named 'app.control.logout_controller'`

```bash
git add tests
git commit -m "test(US02): log out"
git push -u origin feature/US02-logout
```

- [ ] **Step 4: Write the implementation**

`app/control/logout_controller.py`:
```python
from collections.abc import MutableMapping


class LogoutController:
    """US02: log out so nobody else can use the session."""

    def logout(self, session: MutableMapping) -> None:
        session.clear()
```

`app/boundary/auth.py` (replace the whole file):
```python
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import ROLE_HOME, load_current_account
from app.control.errors import LoginError
from app.control.login_controller import LoginController
from app.control.logout_controller import LogoutController

bp = Blueprint("auth", __name__)
bp.before_app_request(load_current_account)


@bp.app_context_processor
def inject_role_home():
    return {"ROLE_HOME": ROLE_HOME}


class LoginPage(MethodView):
    """Boundary for US01: log in."""

    def get(self):
        if g.current_account is not None:
            return redirect(url_for(ROLE_HOME[g.current_account.role]))
        return render_template("auth/login.html")

    def post(self):
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            account = LoginController().login(username, password)
        except LoginError as error:
            return render_template("auth/login.html", error=str(error), username=username)
        session.clear()
        session["account_id"] = account.id
        return redirect(url_for(ROLE_HOME[account.role]))


class LogoutAction(MethodView):
    """Boundary for US02: log out."""

    def post(self):
        LogoutController().logout(session)
        flash("You have been logged out.", "info")
        return redirect(url_for("public.home"))


bp.add_url_rule("/login", view_func=LoginPage.as_view("login"))
bp.add_url_rule("/logout", view_func=LogoutAction.as_view("logout"))
```

`app/boundary/templates/_nav.html` (replace the whole file):
```html
{% if g.current_account %}
  <span class="navbar-text me-3">{{ g.current_account.full_name }}</span>
  <a class="nav-link" href="{{ url_for(ROLE_HOME[g.current_account.role]) }}">Home</a>
  <form method="post" action="{{ url_for('auth.logout') }}" class="d-inline">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <button class="btn btn-link nav-link" type="submit">Log out</button>
  </form>
{% else %}
  <a class="nav-link" href="{{ url_for('auth.login') }}">Log in</a>
{% endif %}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest && ruff check .`
Expected: all tests pass; `All checks passed!`

- [ ] **Step 6: Commit, push (green), merge**

```bash
git add app
git commit -m "feat(US02): log out"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
```

---

### Task 10: US03 Register as customer or interior designer

**Files:**
- Create: `app/control/validation.py`, `app/control/register_controller.py`
- Create: `app/boundary/templates/auth/register.html`
- Modify: `app/boundary/auth.py`, `app/boundary/templates/_nav.html`, `app/boundary/templates/public/home.html`
- Test: `tests/unit/control/test_validation.py`, `tests/unit/control/test_register_controller.py`, `tests/boundary/test_register_page.py`

**Interfaces:**
- Consumes: `UserAccount.create`, `find_by_username`, `find_by_email`; `UserProfile.find_default_for_role`; `ValidationError`
- Produces:
  - `username_problem(str) -> str | None`, `email_problem(str) -> str | None`, `password_problem(str) -> str | None` and `phone_problem(str) -> str | None` in `app.control.validation`
  - `REGISTRABLE_ROLES = ("customer", "designer")`
  - `RegisterController.register(username, email, password, confirm_password, full_name, phone, role) -> UserAccount` (raises `ValidationError`)
  - Endpoint `auth.register` (`/register`)

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b feature/US03-register
```

- [ ] **Step 2: Write the failing tests**

`tests/unit/control/test_validation.py`:
```python
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
```

`tests/unit/control/test_register_controller.py`:
```python
import pytest

from app.control.errors import ValidationError
from app.control.register_controller import RegisterController
from app.entity import db

VALID = {
    "username": "newuser",
    "email": "new@example.com",
    "password": "Passw0rd!",
    "confirm_password": "Passw0rd!",
    "full_name": "New User",
    "phone": "+65 9123 4567",
}


def register(**overrides):
    return RegisterController().register(**{**VALID, "role": "customer", **overrides})


def test_register_customer_uses_default_customer_profile(default_profiles):
    account = register()
    assert account.profile.name == "Customer"
    assert account.check_password("Passw0rd!")


def test_register_designer_uses_default_designer_profile(default_profiles):
    assert register(role="designer").profile.name == "Interior Designer"


def test_register_rejects_admin_role(default_profiles):
    with pytest.raises(ValidationError) as exc:
        register(role="admin")
    assert "role" in exc.value.errors


def test_register_rejects_taken_username(make_account):
    make_account(username="newuser")
    with pytest.raises(ValidationError) as exc:
        register()
    assert exc.value.errors["username"] == "That username is taken."


def test_register_rejects_taken_email_case_insensitively(make_account):
    make_account(email="NEW@example.com")
    with pytest.raises(ValidationError) as exc:
        register()
    assert exc.value.errors["email"] == "An account with that email already exists."


def test_register_rejects_mismatched_confirmation(default_profiles):
    with pytest.raises(ValidationError) as exc:
        register(confirm_password="Different1")
    assert exc.value.errors["confirm_password"] == "Passwords do not match."


def test_register_reports_every_problem_at_once(default_profiles):
    with pytest.raises(ValidationError) as exc:
        register(
            username="x", email="bad", password="short", confirm_password="short", full_name=""
        )
    assert {"username", "email", "password", "full_name"} <= set(exc.value.errors)


def test_register_is_closed_when_default_profile_is_suspended(default_profiles):
    default_profiles["designer"].is_suspended = True
    db.session.commit()
    with pytest.raises(ValidationError) as exc:
        register(role="designer")
    assert exc.value.errors["role"] == "Registration for this role is currently closed."
```

`tests/boundary/test_register_page.py`:
```python
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
```

- [ ] **Step 3: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest`
Expected: `ModuleNotFoundError: No module named 'app.control.validation'`

```bash
git add tests
git commit -m "test(US03): register as customer or interior designer"
git push -u origin feature/US03-register
```

- [ ] **Step 4: Write the control layer**

`app/control/validation.py`:
```python
"""Field rules shared by controllers. Each returns an error message, or None if valid."""

import re

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_]{3,30}")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PHONE_PATTERN = re.compile(r"\+?[0-9 ]{8,15}")


def username_problem(username: str) -> str | None:
    if not USERNAME_PATTERN.fullmatch(username):
        return "Username must be 3-30 letters, digits or underscores."
    return None


def email_problem(email: str) -> str | None:
    if not EMAIL_PATTERN.fullmatch(email):
        return "Enter a valid email address."
    return None


def password_problem(password: str) -> str | None:
    if (
        len(password) < 8
        or not any(c.isalpha() for c in password)
        or not any(c.isdigit() for c in password)
    ):
        return "Password must be at least 8 characters and include a letter and a digit."
    return None


def phone_problem(phone: str) -> str | None:
    if phone and not PHONE_PATTERN.fullmatch(phone):
        return "Phone number must be 8-15 digits, optionally starting with +."
    return None
```

`app/control/register_controller.py`:
```python
from app.control.errors import ValidationError
from app.control.validation import (
    email_problem,
    password_problem,
    phone_problem,
    username_problem,
)
from app.entity import UserAccount, UserProfile

REGISTRABLE_ROLES = ("customer", "designer")


class RegisterController:
    """US03: a visitor registers as a customer or interior designer."""

    def register(
        self, username, email, password, confirm_password, full_name, phone, role
    ) -> UserAccount:
        username, email = username.strip(), email.strip().lower()
        full_name, phone = full_name.strip(), phone.strip()
        errors = {}

        if problem := username_problem(username):
            errors["username"] = problem
        elif UserAccount.find_by_username(username):
            errors["username"] = "That username is taken."

        if problem := email_problem(email):
            errors["email"] = problem
        elif UserAccount.find_by_email(email):
            errors["email"] = "An account with that email already exists."

        if problem := password_problem(password):
            errors["password"] = problem
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if not full_name:
            errors["full_name"] = "Enter your full name."
        if problem := phone_problem(phone):
            errors["phone"] = problem

        profile = None
        if role not in REGISTRABLE_ROLES:
            errors["role"] = "Choose customer or interior designer."
        else:
            profile = UserProfile.find_default_for_role(role)
            if profile is None or profile.is_suspended:
                errors["role"] = "Registration for this role is currently closed."

        if errors:
            raise ValidationError(errors)
        return UserAccount.create(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            profile=profile,
            phone=phone,
        )
```

- [ ] **Step 5: Write the boundary layer**

`app/boundary/auth.py` (replace the whole file):
```python
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from flask.views import MethodView

from app.boundary.auth_guard import ROLE_HOME, load_current_account
from app.control.errors import LoginError, ValidationError
from app.control.login_controller import LoginController
from app.control.logout_controller import LogoutController
from app.control.register_controller import RegisterController

bp = Blueprint("auth", __name__)
bp.before_app_request(load_current_account)


@bp.app_context_processor
def inject_role_home():
    return {"ROLE_HOME": ROLE_HOME}


def _without_passwords(form: dict) -> dict:
    return {key: value for key, value in form.items() if "password" not in key}


class LoginPage(MethodView):
    """Boundary for US01: log in."""

    def get(self):
        if g.current_account is not None:
            return redirect(url_for(ROLE_HOME[g.current_account.role]))
        return render_template("auth/login.html")

    def post(self):
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            account = LoginController().login(username, password)
        except LoginError as error:
            return render_template("auth/login.html", error=str(error), username=username)
        session.clear()
        session["account_id"] = account.id
        return redirect(url_for(ROLE_HOME[account.role]))


class LogoutAction(MethodView):
    """Boundary for US02: log out."""

    def post(self):
        LogoutController().logout(session)
        flash("You have been logged out.", "info")
        return redirect(url_for("public.home"))


class RegisterPage(MethodView):
    """Boundary for US03: register as a customer or interior designer."""

    FIELDS = ("username", "email", "password", "confirm_password", "full_name", "phone", "role")

    def get(self):
        if g.current_account is not None:
            return redirect(url_for(ROLE_HOME[g.current_account.role]))
        return render_template("auth/register.html", form={}, errors={})

    def post(self):
        form = {field: request.form.get(field, "") for field in self.FIELDS}
        try:
            RegisterController().register(**form)
        except ValidationError as error:
            return render_template(
                "auth/register.html", form=_without_passwords(form), errors=error.errors
            )
        flash("Account created. You can log in now.", "success")
        return redirect(url_for("auth.login"))


bp.add_url_rule("/login", view_func=LoginPage.as_view("login"))
bp.add_url_rule("/logout", view_func=LogoutAction.as_view("logout"))
bp.add_url_rule("/register", view_func=RegisterPage.as_view("register"))
```

`app/boundary/templates/auth/register.html`:
```html
{% extends "base.html" %}
{% block title %}Register · {{ config.SITE_NAME }}{% endblock %}
{% block content %}
{% macro field(name, label, type="text") %}
  <div class="mb-3">
    <label class="form-label" for="{{ name }}">{{ label }}</label>
    <input class="form-control{% if errors.get(name) %} is-invalid{% endif %}"
           id="{{ name }}" name="{{ name }}" type="{{ type }}"
           value="{% if type != 'password' %}{{ form.get(name, '') }}{% endif %}">
    {% if errors.get(name) %}<div class="invalid-feedback">{{ errors[name] }}</div>{% endif %}
  </div>
{% endmacro %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <h1 class="h3 mb-3">Create an account</h1>
    <form method="post" novalidate>
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <fieldset class="mb-3">
        <legend class="form-label fs-6">I am a</legend>
        {% for value, label in [("customer", "Homeowner looking for a designer"), ("designer", "Interior designer")] %}
        <div class="form-check">
          <input class="form-check-input" type="radio" name="role" id="role-{{ value }}"
                 value="{{ value }}" {% if form.get('role', 'customer') == value %}checked{% endif %}>
          <label class="form-check-label" for="role-{{ value }}">{{ label }}</label>
        </div>
        {% endfor %}
        {% if errors.get('role') %}<div class="text-danger small">{{ errors['role'] }}</div>{% endif %}
      </fieldset>
      {{ field("username", "Username") }}
      {{ field("email", "Email", "email") }}
      {{ field("full_name", "Full name") }}
      {{ field("phone", "Phone (optional)", "tel") }}
      {{ field("password", "Password", "password") }}
      {{ field("confirm_password", "Confirm password", "password") }}
      <button class="btn btn-primary w-100" type="submit">Create account</button>
    </form>
  </div>
</div>
{% endblock %}
```

`app/boundary/templates/_nav.html` (replace the whole file):
```html
{% if g.current_account %}
  <span class="navbar-text me-3">{{ g.current_account.full_name }}</span>
  <a class="nav-link" href="{{ url_for(ROLE_HOME[g.current_account.role]) }}">Home</a>
  <form method="post" action="{{ url_for('auth.logout') }}" class="d-inline">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <button class="btn btn-link nav-link" type="submit">Log out</button>
  </form>
{% else %}
  <a class="nav-link" href="{{ url_for('auth.login') }}">Log in</a>
  <a class="nav-link" href="{{ url_for('auth.register') }}">Register</a>
{% endif %}
```

`app/boundary/templates/public/home.html` (replace the whole file):
```html
{% extends "base.html" %}
{% block content %}
<div class="py-5 text-center">
  <h1 class="display-5">{{ config.SITE_NAME }}</h1>
  <p class="lead">Find an interior designer whose past work matches your home and budget.</p>
  {% if not g.current_account %}
  <a class="btn btn-primary btn-lg me-2" href="{{ url_for('auth.register') }}">Create an account</a>
  <a class="btn btn-outline-secondary btn-lg" href="{{ url_for('auth.login') }}">Log in</a>
  {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest && ruff check .`
Expected: all tests pass; `All checks passed!`

Manual check: register a designer at `/register`, then log in as them and confirm you land on "Interior Designer home".

- [ ] **Step 7: Commit, push (green), merge**

```bash
git add app
git commit -m "feat(US03): register as customer or interior designer"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
```

---

### Task 11: US44 Change own password

**Files:**
- Create: `app/control/change_password_controller.py`
- Create: `app/boundary/templates/auth/change_password.html`
- Modify: `app/boundary/auth.py`, `app/boundary/templates/_nav.html`
- Test: `tests/unit/control/test_change_password_controller.py`, `tests/boundary/test_change_password_page.py`

**Interfaces:**
- Consumes: `UserAccount.find_by_id`, `check_password`, `change_password`; `password_problem`; `ValidationError`; `login_required`
- Produces: `ChangePasswordController.change_password(account_id, current_password, new_password, confirm_password) -> None` (raises `ValidationError`, or `LookupError` for an unknown account); endpoint `auth.change_password` (`/account/password`)

- [ ] **Step 1: Branch**

```bash
git checkout main && git pull && git checkout -b feature/US44-change-password
```

- [ ] **Step 2: Write the failing tests**

`tests/unit/control/test_change_password_controller.py`:
```python
import pytest

from app.control.change_password_controller import ChangePasswordController
from app.control.errors import ValidationError
from tests.helpers import TEST_PASSWORD


def change(account, current=TEST_PASSWORD, new="N3wPassword", confirm="N3wPassword"):
    ChangePasswordController().change_password(account.id, current, new, confirm)


def test_change_password_updates_the_hash(make_account):
    account = make_account()
    change(account)
    assert account.check_password("N3wPassword")
    assert not account.check_password(TEST_PASSWORD)


def test_rejects_wrong_current_password(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), current="wrong-password")
    assert exc.value.errors["current_password"] == "Current password is incorrect."


def test_rejects_weak_new_password(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), new="short", confirm="short")
    assert "new_password" in exc.value.errors


def test_rejects_reusing_the_current_password(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), new=TEST_PASSWORD, confirm=TEST_PASSWORD)
    assert exc.value.errors["new_password"] == (
        "New password must be different from the current one."
    )


def test_rejects_mismatched_confirmation(make_account):
    with pytest.raises(ValidationError) as exc:
        change(make_account(), confirm="Different1")
    assert exc.value.errors["confirm_password"] == "Passwords do not match."


def test_failed_change_keeps_the_old_password(make_account):
    account = make_account()
    with pytest.raises(ValidationError):
        change(account, current="wrong-password")
    assert account.check_password(TEST_PASSWORD)


def test_unknown_account_raises_lookup_error(app):
    with pytest.raises(LookupError):
        ChangePasswordController().change_password(99999, "a", "b", "c")
```

`tests/boundary/test_change_password_page.py`:
```python
from tests.helpers import TEST_PASSWORD


def test_change_password_requires_login(client, default_profiles):
    assert client.get("/account/password").headers["Location"] == "/login"


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
    assert resp.headers["Location"] == "/customer/"
    client.post("/logout")
    assert login(account.username, "N3wPassword").headers["Location"] == "/customer/"


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
```

- [ ] **Step 3: Run the tests to verify they fail, then commit and push (red)**

Run: `python -m pytest`
Expected: `ModuleNotFoundError: No module named 'app.control.change_password_controller'`

```bash
git add tests
git commit -m "test(US44): change own password"
git push -u origin feature/US44-change-password
```

- [ ] **Step 4: Write the controller**

`app/control/change_password_controller.py`:
```python
from app.control.errors import ValidationError
from app.control.validation import password_problem
from app.entity import UserAccount


class ChangePasswordController:
    """US44: a logged-in user changes their own password."""

    def change_password(
        self, account_id: int, current_password: str, new_password: str, confirm_password: str
    ) -> None:
        account = UserAccount.find_by_id(account_id)
        if account is None:
            raise LookupError(f"No account with id {account_id}")

        errors = {}
        if not account.check_password(current_password):
            errors["current_password"] = "Current password is incorrect."
        if problem := password_problem(new_password):
            errors["new_password"] = problem
        elif new_password == current_password:
            errors["new_password"] = "New password must be different from the current one."
        elif new_password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            raise ValidationError(errors)
        account.change_password(new_password)
```

- [ ] **Step 5: Write the boundary**

In `app/boundary/auth.py`, make three changes.

1. Change the auth_guard import line to:
```python
from app.boundary.auth_guard import ROLE_HOME, load_current_account, login_required
```

2. Add this import after the other `app.control` imports:
```python
from app.control.change_password_controller import ChangePasswordController
```

3. Add this class after `RegisterPage`, and add its URL rule after the existing three:
```python
class ChangePasswordPage(MethodView):
    """Boundary for US44: change own password."""

    decorators = [login_required]

    def get(self):
        return render_template("auth/change_password.html", errors={})

    def post(self):
        try:
            ChangePasswordController().change_password(
                g.current_account.id,
                request.form.get("current_password", ""),
                request.form.get("new_password", ""),
                request.form.get("confirm_password", ""),
            )
        except ValidationError as error:
            return render_template("auth/change_password.html", errors=error.errors)
        flash("Password changed.", "success")
        return redirect(url_for(ROLE_HOME[g.current_account.role]))
```
```python
bp.add_url_rule("/account/password", view_func=ChangePasswordPage.as_view("change_password"))
```

`app/boundary/templates/auth/change_password.html`:
```html
{% extends "base.html" %}
{% block title %}Change password · {{ config.SITE_NAME }}{% endblock %}
{% block content %}
{% macro password_field(name, label) %}
  <div class="mb-3">
    <label class="form-label" for="{{ name }}">{{ label }}</label>
    <input class="form-control{% if errors.get(name) %} is-invalid{% endif %}"
           id="{{ name }}" name="{{ name }}" type="password" required>
    {% if errors.get(name) %}<div class="invalid-feedback">{{ errors[name] }}</div>{% endif %}
  </div>
{% endmacro %}
<div class="row justify-content-center">
  <div class="col-md-5">
    <h1 class="h3 mb-3">Change password</h1>
    <form method="post" novalidate>
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      {{ password_field("current_password", "Current password") }}
      {{ password_field("new_password", "New password") }}
      {{ password_field("confirm_password", "Confirm new password") }}
      <button class="btn btn-primary w-100" type="submit">Change password</button>
    </form>
  </div>
</div>
{% endblock %}
```

`app/boundary/templates/_nav.html` (replace the whole file):
```html
{% if g.current_account %}
  <span class="navbar-text me-3">{{ g.current_account.full_name }}</span>
  <a class="nav-link" href="{{ url_for(ROLE_HOME[g.current_account.role]) }}">Home</a>
  <a class="nav-link" href="{{ url_for('auth.change_password') }}">Change password</a>
  <form method="post" action="{{ url_for('auth.logout') }}" class="d-inline">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <button class="btn btn-link nav-link" type="submit">Log out</button>
  </form>
{% else %}
  <a class="nav-link" href="{{ url_for('auth.login') }}">Log in</a>
  <a class="nav-link" href="{{ url_for('auth.register') }}">Register</a>
{% endif %}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest --cov=app && ruff check .`
Expected: all tests pass; `All checks passed!`

- [ ] **Step 7: Commit, push (green), merge, verify live**

```bash
git add app
git commit -m "feat(US44): change own password"
git push
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --merge --delete-branch
git checkout main && git pull
gh run watch --exit-status
```

On the live Render URL: register a new customer, log in, change the password, log out, and log back in with the new password. Screenshot each step into `evidence/week-1/`. This story is a good candidate for the report's traced CI/CD feature.

---

## Sprint 0 work outside the code

These items happen alongside the tasks and are due before the 12 Oct lab. Assign each one an owner at the first meeting.

- [ ] Register the group with the tutor for your lab: Terence Chew (T01–T04) or Liaw Chun Huei (T05–T08, T01P).
- [ ] Assign the roles in spec section 8.
- [ ] Create the Taiga project (Scrum template, public), add all members, enter all 61 stories with their tasks, and create milestones Sprint 0–5 with the dates in spec section 7.
- [ ] Draw use case diagram v1 covering all four actors and 61 use cases. Save it to `docs/design/`.
- [ ] Write use case descriptions and sequence diagrams for US01, US02, US03 and US44 (definition of done). Each diagram runs boundary → controller → entity, using the class and method names from Tasks 8–11.
- [ ] Draw class diagram v1 from the entities in Tasks 4–6.
- [ ] Bring the six questions in spec section 10 to the 12 Oct lab, and record the answers in that week's minutes.
- [ ] Take minutes for every meeting in `docs/meetings/` using `TEMPLATE.md`.
- [ ] Save end-of-sprint screenshots to `evidence/week-1/`: Taiga backlog, taskboard, burndown chart, the red and green CI runs, and the live app.
