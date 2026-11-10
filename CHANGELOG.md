# Changelog

All notable changes to RenoMatch, newest first. Each entry links to its pull request.
Dates are Singapore time. User story numbers follow the use case deliverables in
`docs/design/use-cases/`.

## Team

| GitHub | Contributor |
|---|---|
| [MeisterKage](https://github.com/MeisterKage) | Team member |
| [sjjt67](https://github.com/sjjt67) | Team member |
| [KeefeLiew](https://github.com/KeefeLiew) | Team member |
| [jerrits69](https://github.com/jerrits69) | Team member |

## 10 Nov 2026

### Removed the separate role home pages ([#20](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/20))

- Every role now lands on the website home page after logging in.
- The old `/admin/` and `/platform/` addresses redirect to the home page.
- The home page hero shows each role's main link: User accounts for the user admin and Project categories for the platform manager.
- The role home template, its tool lists and their styles are removed, along with the footer Your home link.
- Every tool stays in the menu and Change password stays on the account page, so every user story is still reachable.
- Added this changelog and the team list in the README.

## 7 Nov 2026

### US-13 sequence diagram wording ([#19](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/19))

- Step 1 of the US-13 sequence diagram now reads click "Compare" on an IDP, matching the single Compare button on the site.

### Exact wording from the sequence diagrams ([#18](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/18))

- US-32: Audit Log in the menu and the page heading.
- US-13: the button on a design and the menu link read Compare, with the number selected shown as a small badge.
- New test: every label quoted in a sequence diagram must appear on the site with the same wording.

### Wrap-up ([#17](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/17))

- Role menus, with the account name beside Log out.
- Customers and designers land on the website home page after logging in.
- Comparing needs an account, and visitors see a reminder to log in.
- Removed sprint labels, Available badges and extra footer text.
- Designs from suspended accounts or profiles are hidden from every public page, favourites and enquiries.
- Search wildcards are escaped.

## 4 Nov 2026

### US-60 Feature IDPs and US-58 Review Reported IDPs ([#16](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/16))

- Platform managers feature up to six designs on the home page and unfeature them.
- Platform managers uphold a report, which removes the design, or dismiss it.
- All 12 diagrammed use cases are now checked by the diagram conformance test.

### Categories and reports, with US-54 and US-56 ([#15](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/15))

- Platform managers create, view, update, suspend, reactivate and search categories (US-54).
- Daily, monthly (US-56) and custom range activity reports, each with a PDF export.

### US-43 View Count and US-48 Weekly Email ([#14](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/14))

- Designers see the view count (US-43) and shortlist count of each design.
- Interest dashboard across the whole portfolio.
- Weekly summary email to opted-in designers (US-48), run by a scheduled GitHub workflow, a CLI command or a protected endpoint.

### Company info and portfolio, with US-38 Add IDP ([#13](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/13))

- Designers create, view and update their company information.
- Designers add designs with photos (US-38), then view, edit, remove and search them.
- Photo uploads accept JPG and PNG files up to 5 MB.

### Admin profiles, US-32 Audit Log and US-34 Export CSV ([#12](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/12))

- User admins create, view, update, suspend, reactivate and search user profiles.
- Audit Log of admin actions filtered by date range (US-32).
- Export the matching accounts as a CSV file (US-34).

## 3 Nov 2026

### Admin user accounts, lockout and unlock ([#11](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/11))

- User admins create, view, update, suspend, reactivate and search user accounts.
- Five failed logins lock an account for 15 minutes, and admins can unlock it.
- Every admin change is written to the audit log.

### US-05 Reset Password and account details ([#10](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/10))

- Forgotten passwords are reset with a single-use emailed link that expires in one hour (US-05).
- Every user can update their account details or delete their account.

### US-12 Recommended IDPs and US-13 Compare IDPs ([#9](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/9))

- Recommendations based on what a customer has viewed and saved, with popular designs for new customers (US-12).
- Compare up to three designs side by side (US-13).
- Visitors see six featured designs on the home page.

### Enquiries and US-19 Review Designer ([#8](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/8))

- Customers send enquiries about a design, and customers and designers reply in the same conversation.
- Customers rate and review a designer they have contacted (US-19).

### Favourites ([#7](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/7))

- Customers save designs to favourites with a note, then view, search and remove them.

### Browse, search and designer profiles ([#6](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/6))

- Browse page with photo cards and filters for keyword, category, style, property type and budget.
- Design pages with a photo gallery and view counting.
- Designer profiles with company information, portfolio and average rating.

### Entity names from the diagrams ([#5](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/5))

- Every entity class, attribute and method now uses the names from the use case diagrams.
- New diagram conformance test checks the code against the sequence diagrams.

### Diagram deliverables and build plan ([#4](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/4))

- Added the team's use case deliverables as the reference the code must match.
- Added the full build spec and plan, and the interior photos used by the test data.

## 3 Oct 2026

### Photo-led redesign ([#3](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/3))

- Full-screen interior photo hero, Browse by style gallery and How it works steps.

### Site design ([#2](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/2))

- RenoMatch's own stylesheet and typeface in place of Bootstrap.

### Deploy to Render ([#1](https://github.com/MeisterKage/CSIT314-RenoMatch/pull/1))

- The site deploys to Render automatically after the GitHub checks pass.

### Sprint 0 foundations

- Flask app with Boundary, Control and Entity layers.
- Entities, generated test data with over 100 rows of each type, and demo accounts.
- Log in, log out, register and change password.
- GitHub Actions running the linter and tests on every change.
