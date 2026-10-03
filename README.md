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
