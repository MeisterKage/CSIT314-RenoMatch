# Renovation Matching Platform — Design Spec

**Course:** CSIT314 Software Development Methodologies, SIM S4 2026, group project (40 marks)
**Date:** 2026-10-03
**Status:** Agreed design, pending group review

## 1. Goal

Build a web platform that matches renovation customers with interior designers (reference: www.sixides.com). Four actor types: User Admin, Interior Designer (ID), Customer, Platform Management. The group commits to building all 61 user stories in section 3, ordered so that every spec-required story is finished by 1 Nov and later stories are the first to cut if the schedule slips.

### Deadlines

| Date | Event |
|---|---|
| 12 Nov 2026, 23:59 | Final report, recorded live-demo video, source code to Moodle (35 marks). Internal target: submit 11 Nov. |
| 16 Nov 2026 (last lab) | Final presentation: demo video + Q&A (5 marks) |

### Constraints from the project specification

- Backend must be object-oriented.
- Design must follow the Boundary–Control–Entity (B-C-E) framework.
- Test data of at least ~100 records per data type, script-generated; the live demo runs on it.
- Agile method (Scrum), weekly sprints, Taiga public project, weekly evidence screenshots.
- Test-driven development and CI/CD, with evidence.
- The tutor is the client: requirements are elicited from and demonstrated to them each week, and may change.

## 2. Technology decisions

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Strongest shared skill in the group |
| Web framework | Flask, server-rendered Jinja templates, Bootstrap | One codebase; each boundary is a route + template, so code maps 1:1 to sequence diagrams |
| Persistence | SQLite via SQLAlchemy | Zero setup, fresh DB per CI run; SQLAlchemy allows a later switch to PostgreSQL without changing entities |
| Tests | pytest, pytest-cov, Flask test client | Simple TDD loop, coverage reported in CI |
| Lint | ruff | Fast, single tool |
| Test data | Faker-based `scripts/seed.py` | Repeatable random data at the required scale |
| CI | GitHub Actions | Runs on every push and PR |
| CD | Render free web service, deployed via deploy hook from GitHub Actions | Only green builds on `main` go live |
| Email | SMTP (e.g. Gmail app password) in production; console backend in dev and tests | US43, US52 |
| Agile tool | Taiga (public project) | Recommended by the subject |

### Hosting caveat (Render free tier, checked 3 Oct 2026)

- Service spins down after 15 minutes without traffic; spin-up takes about a minute.
- The filesystem, including the SQLite file and any uploaded files, is wiped on every redeploy, restart or spin-down.
- Free Postgres expires 30 days after creation, so it is not used.
- 750 free instance hours per workspace per month.

Consequences: the app runs the seed script on startup when the database is empty; IDP photos are stored in the database, not on disk; the recorded final demo is run locally from the deployed commit, or the deployed site is warmed and kept active for the whole recording.

## 3. User stories

Full wording is kept in Taiga. "Sprint" refers to section 7. US61 was added during design so that US58 has an input.

### User / Visitor

| ID | Story | Sprint |
|---|---|---|
| US01 | Log in with username and password | 0 |
| US02 | Log out | 0 |
| US03 | Visitor registers as customer or interior designer | 0 |
| US43 | Reset forgotten password via emailed link | 4 |
| US44 | Change own password | 0 |
| US45 | Visitor browses IDPs without an account | 3 |

### User Admin

| ID | Story | Sprint |
|---|---|---|
| US04 | Create user account | 1 |
| US05 | View user account | 1 |
| US06 | Update user account | 1 |
| US07 | Suspend user account | 1 |
| US08 | Reactivate user account | 1 |
| US09 | Search user accounts by keyword, profile, status | 1 |
| US10 | Create user profile | 1 |
| US11 | View user profile (role, account count) | 1 |
| US12 | Update user profile | 1 |
| US13 | Suspend user profile (blocks all its accounts) | 1 |
| US14 | Reactivate user profile | 1 |
| US15 | Search user profiles by keyword, role, status | 1 |
| US46 | View audit log of admin actions | 4 |
| US47 | View failed logins and unlock locked accounts | 4 |
| US48 | Export user account list as CSV | 4 |

### Interior Designer

| ID | Story | Sprint |
|---|---|---|
| US16 | Create company information | 1 |
| US17 | View company information | 1 |
| US18 | Update company information | 1 |
| US19 | Add IDP to portfolio | 2 |
| US20 | View own IDP | 2 |
| US21 | Update own IDP | 2 |
| US22 | Remove IDP from portfolio (soft delete / archive) | 2 |
| US23 | Search own IDPs | 2 |
| US24 | See view count of an IDP | 3 |
| US25 | See shortlist count of an IDP | 3 |
| US49 | Upload photos to an IDP | 2 |
| US50 | Portfolio-wide interest dashboard | 5 |
| US51 | Receive and reply to customer enquiries | 5 |
| US52 | Weekly email summary of views and shortlists | 5 |

### Customer

| ID | Story | Sprint |
|---|---|---|
| US26 | Search IDPs by keyword, category, style, property type, budget | 3 |
| US27 | View IDP details | 3 |
| US28 | View designer's company profile and portfolio | 3 |
| US29 | Save IDP to favourites with optional note | 3 |
| US30 | View favourites list | 3 |
| US31 | Remove IDP from favourites | 3 |
| US32 | Search favourites | 3 |
| US42 | "Recommended for you" IDPs (also the data-driven feature) | 5 |
| US53 | Send enquiry to a designer about an IDP | 5 |
| US54 | Compare up to three IDPs side by side | 5 |
| US55 | Rate and review a designer (only after the designer has replied to the customer's enquiry) | 5 |
| US56 | Update own name, email, phone (extended to all roles) | 4 |
| US57 | Delete own account and personal data (PDPA) | 5 |
| US61 | Report an inappropriate IDP | 4 |

### Platform Management

| ID | Story | Sprint |
|---|---|---|
| US33 | Create IDP category | 2 |
| US34 | View category (with project count) | 2 |
| US35 | Update category | 2 |
| US36 | Suspend category | 2 |
| US37 | Reactivate category | 2 |
| US38 | Search categories | 2 |
| US39 | Daily activity report | 3 |
| US40 | Weekly activity report | 3 |
| US41 | Monthly activity report | 3 |
| US58 | Review reported IDPs and remove inappropriate ones | 5 |
| US59 | Activity report for a custom date range | 3 |
| US60 | Feature selected IDPs on the home page | 4 |

Before stories are entered into Taiga, the group may renumber them by role; sequence diagrams, tests and branch names then use the final IDs.

## 4. Architecture

```
app/
  __init__.py   Flask app factory, config, DB init, seed-on-empty
  boundary/     one blueprint per role (auth, admin, designer, customer, platform)
    templates/  Jinja templates, one per page
  control/      one controller class per user story
  entity/       SQLAlchemy entity classes with domain and persistence methods
scripts/
  seed.py       Faker test data
tests/
  unit/         entity and controller tests
  boundary/     Flask test-client tests per page
.github/workflows/
  ci.yml        lint + tests on push and PR; deploy hook on main
  weekly.yml    scheduled call for US52
evidence/
  week-N/       weekly screenshots for the report
```

### Layering rules

1. A boundary only reads input, calls one controller, and renders the result.
2. A controller only calls entities. It holds the story's application logic and validation.
3. An entity owns its data and its persistence (for example `UserAccount.find_by_id()`, `UserAccount.suspend()`).
4. No layer is skipped. Each story is exactly one boundary → controller → entity chain, and that chain is the story's sequence diagram.

Example, US07: `SuspendUserAccountPage` → `SuspendUserAccountController.suspend(account_id)` → `UserAccount.suspend()`.

Rule 3 follows the B-C-E style usually taught in CSIT314. It will be checked against the lecture materials once they are added to the repo. If those place persistence in a separate class, the design follows the lecture style instead.

### Cross-cutting behaviour

- **Authentication and roles:** session-based login; a role check on every route; suspended accounts or accounts with a suspended profile cannot log in.
- **Passwords:** stored as salted hashes (werkzeug.security). Never stored or logged in plain text.
- **Lockout (US47):** 5 consecutive failed logins lock the account for 15 minutes, or until an admin unlocks it.
- **Audit (US46):** every User Admin controller writes an AuditLog entry.
- **Soft deletion:** suspend, archive and remove actions set flags; rows are not deleted, so event history and reports stay correct. US57 anonymises personal fields instead of deleting the customer's event rows.

## 5. Data model

| Entity | Key fields | Used by |
|---|---|---|
| UserProfile | name, description, role_type (admin / designer / customer / platform), is_suspended | US10–15 |
| UserAccount | username, email, password_hash, full_name, phone, profile_id, is_suspended, failed_logins, locked_until, is_anonymised, created_at | US01–09, 44, 47, 56, 57 |
| PasswordResetToken | account_id, token_hash, expires_at, used_at | US43 |
| LoginAttempt | username, account_id (nullable), success, attempted_at | US47 |
| CompanyInfo | designer_id (unique), name, description, address, phone, email, website | US16–18, 28 |
| Category | name, description, is_suspended | US33–38 |
| IDP | designer_id, category_id, title, description, style, property_type, budget, location, status (current / past), completed_on, is_archived, is_featured, is_removed, created_at | US19–23, 26, 58, 60 |
| IDPPhoto | idp_id, image data, caption, position | US49 |
| Favourite | customer_id, idp_id, note, saved_at; unique (customer_id, idp_id) | US29–32 |
| ViewEvent | idp_id, viewer_id (null for visitors), viewed_at | US24, 42, 45, 50 |
| ShortlistEvent | idp_id, customer_id, shortlisted_at; never deleted | US25, 50 |
| Enquiry | customer_id, designer_id, idp_id (nullable), subject, created_at | US51, 53, 55 |
| EnquiryMessage | enquiry_id, sender_id, body, sent_at | US51, 53 |
| Review | customer_id, designer_id, rating (1–5), comment, created_at | US55 |
| IDPFlag | idp_id, reporter_id, reason, status (open / upheld / dismissed), reviewed_by, reviewed_at | US58, 61 |
| AuditLog | actor_id, action, target_type, target_id, details, created_at | US46 |

**Computed on demand (entity classes without tables):**

- `PlatformReport`: built for a date range from accounts, IDPs, events and enquiries (US39–41, 59).
- `Recommender`: ranks IDPs for a customer from their views, favourites and categories (US42).
- The comparison list (US54) is held in the user's session.

**Rules fixed by this design (until the tutor says otherwise):**

- "Times shortlisted" = count of ShortlistEvents. Removing a favourite does not reduce it.
- Visitor views count toward an IDP's view total.
- A customer can review a designer only if that designer has replied to at least one of the customer's enquiries.
- Suspended categories, and archived or removed IDPs, are hidden from customer and visitor search.

**Test data:** at least 100 rows for each main entity. Thousands of ViewEvents and ShortlistEvents spread over the previous 90 days, so daily, weekly and monthly reports show trends. The seed script is deterministic when given a fixed random seed.

## 6. Testing and CI/CD

### TDD workflow per story

1. Branch `feature/USxx-short-name` from `main`.
2. Red: commit tests only, e.g. `test(US07): suspended account cannot log in`. CI runs and fails; this is the timestamped evidence.
3. Green: commit the implementation, e.g. `feat(US07): suspend user account`. CI passes.
4. Refactor with tests green.
5. Open a PR; merge only when CI passes.

### Test layers

- Unit: entity methods and controllers against an in-memory SQLite database, fresh per test.
- Boundary: Flask test client posts forms, checks responses, redirects and role restrictions.
- Seed: verifies the seed script produces at least 100 records per main entity and that they pass validation.
- The report's test plan lists test cases per story (ID, story, input, expected, actual), traced to pytest function names.

### Pipeline

- `ci.yml`, on every push and PR: install, `ruff check`, `pytest --cov`.
- On push to `main` with tests passing: call the Render deploy hook (GitHub secret). Render auto-deploy is off.
- `weekly.yml`, scheduled weekly: calls a token-protected endpoint that sends US52 summaries.
- Branch protection on `main`: PR required, CI must pass, no direct pushes.

### CD evidence

One feature is traced with screenshots: Taiga card → branch → failing CI run → passing CI run → merged PR → deploy run → feature live on the Render URL.

## 7. Sprint plan

Each sprint ends the day before a lab; the lab is the sprint review with the tutor.

| Sprint | Dates | Lab demo | Stories | Other work |
|---|---|---|---|---|
| 0 | 3–11 Oct | Mon 12 Oct | US01–03, US44 | Repo and branch protection, Taiga with all stories and tasks, CI/CD deploying a skeleton app, all entity classes, seed script, first use case diagram, questions for the tutor |
| 1 | 12–19 Oct | Tue 20 Oct | US04–18 | |
| 2 | 20–25 Oct | Mon 26 Oct | US19–23, US49, US33–38 | |
| 3 | 26 Oct–1 Nov | Mon 2 Nov | US24–32, US45, US39–41, US59 | All spec-required stories complete |
| 4 | 2–4 Nov | Thu 5 Nov | US43, 46, 47, 48, 56, 60, 61 | Short sprint: small stories only. Draft ethics section |
| 5 | 5–11 Nov | Thu 12 Nov | US42, 50–55, 57, 58 | Code freeze end of 9 Nov. 10–11 Nov: bug fixes, demo recording, report finalisation, signatures, submit 11 Nov. Data-driven plan (US42) written |
| — | — | Mon 16 Nov | — | Final presentation |

Sprint 5 stories are not required by the specification. If the group is behind at the 5 Nov lab, they are cut in this order: US55, US54, US52, US50, US51/53, US58, US57, US42 (US42 then remains a plan only).

Order within sprints: US61 before US58; US43 (email infrastructure) before US52; US51/53 before US55.

### Definition of done

- Tests committed before implementation; CI green.
- PR merged and deployed.
- Use case description and sequence diagram written; class diagram updated.
- Taiga card closed with tasks ticked.

### Weekly routine

- Lab: sprint review with the tutor; record their feedback.
- Same week: retrospective and next sprint planning.
- End of sprint: screenshots of Taiga backlog, sprint board, burndown chart and running app saved to `evidence/week-N/`.
- Every meeting: minutes from a fixed template (date, attendance, progress, backlog snapshot, discussion, action items).

## 8. Roles

Each role is held in addition to developing stories. Every member implements stories so that contribution is visible in git and Taiga.

| Role | Responsibility |
|---|---|
| Product Owner | Tutor liaison, backlog ordering, acceptance of stories |
| Scrum Master | Runs meetings, writes minutes, collects weekly evidence |
| DevOps lead | GitHub Actions, Render, secrets, branch protection |
| Test lead | Test plan, test data, TDD evidence |
| Design lead | UML consistency across diagrams and against code |
| Report editor | Assembles the report, collects contribution ratings and signatures |

## 9. Report contents (mapped to the marking scheme)

| Report section | Marks it supports |
|---|---|
| User stories with tasks (all 61) | User stories and tasks (8) |
| Use case diagram(s), use case descriptions, sequence diagrams, class diagrams, data persistence (ER diagram, section 5), UI screenshots | Analysis and design (9) |
| Code structure and how it maps to B-C-E | Implementation (8), design consistency |
| Test plan, test cases, test data, TDD evidence | TDD (2) |
| CI/CD pipeline and traced feature | CI/CD (2) |
| Ethics: privacy and PDPA (US57), password hashing, audit trail (US46), fairness of featured listings (US60) and recommendations (US42), moderation (US58, US61) | Ethics (1) |
| Data-driven development plan for US42 | Data-driven (1) |
| Taiga evidence, weekly screenshots, meeting minutes | Methodology (2) |
| Cover page: contribution rating and justification per member, all signatures | Required for individual marks |

## 10. Open questions for the tutor (Sprint 0)

1. Do self-registered interior designers (US03) need admin approval before their portfolio is public?
2. Should removing a favourite reduce an IDP's "times shortlisted" count? (Design assumes no.)
3. Should views by visitors who are not logged in count? (Design assumes yes.)
4. What should the daily, weekly and monthly reports contain? Proposed: new accounts by role, new IDPs, views, shortlists, enquiries, top IDPs, categories and designers.
5. Are progress or mid-project reports required? The cover-page section mentions them; the submission list does not.
6. Is IDP deletion (US22) acceptable as archiving?

Answers are recorded in meeting minutes and reflected in Taiga.

## 11. Risks

| Risk | Mitigation |
|---|---|
| 61 stories in 5.5 weeks | Spec-required stories finish by 1 Nov; sprint 5 stories have a cut order |
| Design and code drift apart | Diagrams are part of the definition of done for each story |
| Evidence missing at the end | Weekly evidence folder and minutes template from sprint 0 |
| Render wipes data or sleeps during demo | Seed on startup; record the demo locally or keep the site warm |
| Lecture B-C-E style differs from this design | Check lecture materials in sprint 0 and adjust before entity classes are written |
| Email delivery fails in the demo | Console email backend as a fallback; show the email in logs |
