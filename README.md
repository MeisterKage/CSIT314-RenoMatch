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

## Test data and demo accounts

On startup the app fills an empty database with generated data: 100+ rows per main entity,
plus about 8,000 views and 1,500 shortlists spread over the last 90 days.
To rebuild it locally: `flask --app app seed --reset`.

After pulling changes to entity classes, rebuild your local database with
`flask --app app seed --reset` (there are no migrations).

Every seeded account's password is `Password123!`.

| Role | Username |
|---|---|
| User Admin | `admin` |
| Platform Manager | `manager` |
| Interior Designer | `designer` |
| Customer | `customer` |

## Deployment

Hosted on Render's free plan, defined in `render.yaml` (a Render Blueprint).
Render deploys `main` automatically, but only after the GitHub Actions checks
(lint + tests) pass. No deploy hook or secret is involved.

The free plan wipes the disk on every deploy, restart and spin-down (after 15 idle
minutes), so the app re-creates its test data on startup. Anything created on the
live site is temporary, and the first visit after idling takes about a minute.
