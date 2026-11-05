# RenoMatch

CSIT314 group project: a platform that matches renovation customers with interior designers.
Design spec: `docs/specs/2026-10-03-renovation-platform-design.md`.

## Features by role

| Role | What they can do |
|---|---|
| Visitor | Browse and search designs, view a design with its photos, view a designer profile and reviews, register, log in, reset a forgotten password |
| Customer | Save favourites with a note, search favourites, compare up to 3 designs, get recommendations, send enquiries and read replies, rate and review a designer, update account details, change password, delete account |
| Interior Designer | Manage company information, add, update, delete and search portfolio projects with photos, see views and shortlists per project, see the interest dashboard, reply to enquiries, receive a weekly summary email |
| User Admin | Create, view, update, suspend, reactivate, unlock and search accounts and profiles, export accounts to CSV, read the audit log |
| Platform Manager | Manage project categories, run daily, monthly and custom activity reports with a PDF export, feature projects on the home page, review and resolve reported projects |

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

| Role | Username | Password |
|---|---|---|
| User Admin | `admin` | `Password123!` |
| Platform Manager | `manager` | `Password123!` |
| Interior Designer | `designer` | `Password123!` |
| Customer | `customer` | `Password123!` |

## Configuration

All settings are environment variables. None is needed to run locally.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs sessions. Required in production |
| `DATABASE_URL` | Database location. Defaults to a SQLite file in `instance/` |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_SENDER` | SMTP settings for password reset and weekly summary emails. When any one is missing, emails are written to the application log instead of being sent |
| `WEEKLY_SUMMARY_TOKEN` | Shared secret for `POST /internal/weekly-summary`, sent in the `X-Summary-Token` header. When it is not set the endpoint is disabled |

The weekly summary can also be sent by hand with `flask --app app send-weekly-summaries`.
The workflow `.github/workflows/weekly-summary.yml` calls the endpoint every Monday at
01:00 UTC. It needs two GitHub repository secrets: `RENDER_APP_URL` (the live site's base URL)
and `WEEKLY_SUMMARY_TOKEN` (the same value as the app's variable).

## Traceability

`docs/design/traceability.md` maps every class, attribute and method in the 12 diagrammed
use cases to the file and line that implements it. Regenerate it with
`python scripts/traceability.py` after changing a diagrammed class.
`tests/test_diagram_conformance.py` fails when the code drifts from the class diagrams.

## Deployment

Hosted on Render's free plan, defined in `render.yaml` (a Render Blueprint).
Render deploys `main` automatically, but only after the GitHub Actions checks
(lint + tests) pass. No deploy hook or secret is involved.

The free plan wipes the disk on every deploy, restart and spin-down (after 15 idle
minutes), so the app re-creates its test data on startup. Anything created on the
live site is temporary, and the first visit after idling takes about a minute.
