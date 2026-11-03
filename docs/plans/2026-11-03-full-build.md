# Full Build Implementation Plan (US-01 to US-60)

**Goal:** Build all 60 Final Report user stories. The 12 diagrammed use cases must match `docs/design/use-cases/` exactly, and CI verifies this.

**Spec:** `docs/specs/2026-11-03-full-build-design.md`. Read sections 2 (naming), 3 (entities) and 7 (rules) before any task.

**Architecture:** Flask app in Boundary-Control-Entity layers, as before. Entities are camelCase SQLAlchemy models named `<Name>Entity`. Controllers hold `self.entity`. Boundaries are `MethodView` pages that hold `self.controller` and render through `display...()` methods.

**Tech:** Python 3.12+, Flask 3.1, Flask-SQLAlchemy, Flask-WTF, Faker, fpdf2 (new, for US-57), pytest and ruff.

## Global Constraints

- Names: classes, attributes, methods and parameters copy the diagram text extracts (`docs/design/use-cases/US-xx/US-xx_diagram_text.md`) character for character. camelCase is deliberate.
- Private diagram methods (`-`) keep their exact name with no leading underscore. The docstring starts with `Private:`.
- Boundaries hold `self.controller`. Controllers hold `self.entity` (the entity class), and `self.emailService` where the diagram has it. Entity methods called by controllers are `@classmethod`s.
- Each diagrammed controller method makes the diagram's entity calls in the diagram's order, under the diagram's guards.
- Status strings: `"Active"`, `"Suspended"`, `"Removed"`; flags use `"Open"`, `"Upheld"`, `"Dismissed"`.
- Every form carries `csrf_token`. Pages need the right role through `role_required`.
- Messages shown to users use the exact wording in spec section 7.
- TDD: commit the failing tests first (`test(US-xx): ...`), then the implementation (`feat(US-xx): ...`). The full suite and ruff must pass before the final commit.
- No AI attribution in commits or files. Never stage `Final Report.pdf`, `Use_Case_Deliverables_PNG.zip`, `docs/reference/`, `.venv/` or `instance/`.
- UI: use the existing design system (`app/boundary/static/site.css`, `base.html`, `_field.html`). Add CSS only through new classes in `site.css`, and keep pages consistent with the current look.

## Conformance test (built in Task 1, extended by each task)

`tests/test_diagram_conformance.py` parses every `docs/design/use-cases/US-*/US-*_diagram_text.md` listed in `CONFORMING_USE_CASES` (a list at the top of the test file).

For each class box (a `«boundary»`, `«control»` or `«entity»` line followed by its attribute line and method line), it:
1. finds the Python class with that exact `__name__` by importing every module under `app`;
2. checks each `- name: Type` attribute exists:
   - entities: `hasattr(cls, name)` (columns and properties both count)
   - boundaries and controllers: `hasattr(cls(), name)` (instance attributes)
3. checks each `+`/`-` method `name(p1: T, p2: T)` exists on the class, with parameter names (excluding self and cls) equal to `[p1, p2]` in order.

Each task appends its diagrammed use case IDs to `CONFORMING_USE_CASES`, so CI enforces the diagrams from then on.

## Execution

Work tasks in order. Each task gets a branch `feature/<slug>`. The implementer commits test-first and stops on the branch. The controller reviews it, pushes it, opens a PR, waits for CI and merges with a merge commit, which Render then deploys.

---

### Task 1: Entity refactor to diagram naming, plus the conformance harness

**Branch:** `feature/entity-refactor`

**Do:**
1. Rewrite `app/entity/` to the entity model in spec section 3: `<Name>Entity` classes with camelCase attributes, mapped to DB columns with `db.Column("snake_name", ...)` where useful.
   - Remove `PasswordResetToken`, `IDPPhoto`, `ViewEvent` and `ShortlistEvent`.
   - Add `PlatformActivityEntity`, and `app/entity/reports.py` with the `Report` and `Summary` dataclasses (fields as needed by US-48, 55, 56 and 59; simple typed fields).
   - Replace the boolean suspend flags with `status` strings.
   - Add `IDPEntity.photoUrls` (JSON list), `stage`, `featuredDate`, `viewCount` and `shortlistCount`, and `UserAccountEntity.resetToken`, `tokenExpiry` and `weeklySummaryOptIn`.
   - Add `CategoryEntity.idpCount` as a property counting Active IDPs.
2. Rename the existing entity methods to camelCase: `createUserAccount`, `findById`, `findByUsername`, `findByEmail`, `setPassword`, `checkPassword`, `changePassword`, `canLogIn`, `createUserProfile`, `findByName`, `findDefaultForRole`. Keep their behaviour, including lowercasing usernames and emails.
3. Update every existing controller, boundary, template, the seed (`app/seed.py`) and every test to the new names. Behaviour stays the same: login, logout, register, change password, the role homes and the seed counts.
4. Update the seed to spec section 4 in full:
   - `photoUrls` from `/static/img/idp/idp-NN.jpg`, 1–3 per IDP, deterministic
   - PlatformActivity rows for view, shortlist, register, enquiry and review
   - counters equal to the activity counts
   - exactly 6 featured IDPs with `featuredDate`
   - opt-out and status mixes as specified
   - the seed tests updated to cover these
5. Build `tests/test_diagram_conformance.py` as described above, with `CONFORMING_USE_CASES = []`. Add a self-test that runs the parser on `US-32` and asserts it finds the classes `AuditLogPage`, `ViewAuditLogController` and `AuditLogEntity`, and that `AuditLogEntity` has an attribute named `timestamp`. That attribute exists after this task, so this also proves the attribute check works.
6. Add `fpdf2>=2.7` to `requirements.txt`. (It's used in Task 14; adding it now avoids a second dependency change.)

**Tests:** all existing behaviour tests pass under the new names. There are new entity tests for the status strings, `idpCount`, the counters, `photoUrls` and `PlatformActivityEntity`, plus the conformance self-test.

### Task 2: Visitor and customer browsing (US-01, US-09, US-10, US-11)

**Branch:** `feature/browse-idps`

**Do:**
- `BrowseIDPsPage` (`/idps`, public): a photo-card grid of Active IDPs, paginated at 24.
- Filters for keyword (title or description), category, style, propertyType and minBudget/maxBudget (US-09). These go through `SearchIDPsController.searchIDPs(keyword, categoryId, style, propertyType, minBudget, maxBudget)` → `IDPEntity.searchIDPs(...)`.
- `BrowseIDPsController.getActiveIDPs(page)` for the unfiltered list (US-01).
- `IDPDetailsPage` (`/idps/<idpId>`, public): photos, details, the designer link, and a "Compare" checkbox form posting to `/compare/select` (Task 5 handles it; render the control now).
- `ViewIDPDetailsController.viewIDPDetails(idpId, viewerId)` → `IDPEntity.recordView(idpId, viewerId)`. This adds a view activity and increments viewCount unless the viewer is the IDP's own designer, then returns the IDP. Suspended or Removed IDPs give 404.
- `DesignerProfilePage` (`/designers/<designerId>`, public): company info, the Active portfolio grid and the average rating with reviews. The review form part comes in Task 4, so leave a clearly marked spot.
- `ViewDesignerProfileController.viewDesignerProfile(designerId)`.
- Navigation: add "Browse designs" to `_nav.html`. The home page "Browse by style" cards link to `/idps?style=<Style>`.

**Tests:** filters (each one), pagination, the view counter (counts a customer view, not the designer's own), 404 for non-Active IDPs, and that the profile shows the average rating.

### Task 3: Favourites (US-14, US-15, US-16, US-17)

**Branch:** `feature/favourites`

**Do:**
- `POST /idps/<idpId>/favourite`, with an optional `note`: `SaveFavouriteController.saveFavourite(userId, idpId, note)` → `FavouriteEntity.saveFavourite(...)`. This adds a shortlist activity and increments `shortlistCount`. Saving an IDP that's already saved updates the note.
- `FavouritesPage` (`/favourites`, customers): lists favourites with notes.
  - `ViewFavouritesController.getFavourites(userId)`
  - remove: `RemoveFavouriteController.removeFavourite(userId, idpId)`
  - search: `SearchFavouritesController.searchFavourites(userId, keyword)`
- The save form sits on `IDPDetailsPage` (customers only).

**Tests:** save, the counter increments, saving twice updates the note, remove doesn't decrement, search, and other roles get 403.

### Task 4: Enquiries and reviews (US-18, US-47, US-19 diagrammed)

**Branch:** `feature/enquiries-reviews`

**Do:**
- US-18: `POST /idps/<idpId>/enquiry` (customer, with subject and message) → `SendEnquiryController.sendEnquiry(userId, idpId, subject, message)`. This creates the Enquiry and its first message, and an enquiry activity.
- US-47: `EnquiriesPage` (`/designer/enquiries`, `/designer/enquiries/<enquiryId>`).
  - `ViewEnquiriesController.getEnquiries(designerId)` and `getEnquiryThread(enquiryId, designerId)`
  - `ReplyEnquiryController.replyEnquiry(enquiryId, designerId, body)`
  - Customers see their own threads at `/enquiries`, reusing the same controllers through a customer-side method.
- **US-19 is exact to `docs/design/use-cases/US-19`:**
  - `DesignerProfilePage` gets `displayReviewForm(existingReview=None)`, `displayReview()` and `displayMessage()`.
  - `RateReviewDesignerController` has `submitReview(designerId, userId, rating, comment)` and `checkEligibility(designerId, userId)`.
  - `ReviewEntity` has `submitReview`, `getAverageRating(designerId)` and `checkEligibility(designerId, userId)`.
  - The rules are in spec section 7. Eligible means the user has at least one Enquiry with that designer.
  - Re-submitting an existing review updates it.
  - Order of calls in `submitReview`: `entity.submitReview(...)`, then `entity.getAverageRating(designerId)` if that returned true. A review activity is recorded.
- Append `"US-19"` to `CONFORMING_USE_CASES`.

**Tests:** each US-19 `alt` branch (eligible, not contacted, already reviewed, invalid rating or comment), the average rating updates, plus US-18 and US-47 flows and permissions.

### Task 5: Compare and recommendations (US-13, US-12, both diagrammed)

**Branch:** `feature/compare-recommend`

**Do:**
- **US-13 is exact to `docs/design/use-cases/US-13`:**
  - Selection lives in the session: `POST /compare/select` (add, refused with the 1a message when 3 are already selected), `POST /compare/clear`, `GET /compare`.
  - `CompareIDPPage` has `displayComparison()` and `displayMessage()`.
  - `CompareIDPsController.compareIDPs(idpIds)` → `IDPEntity.compareIDPs(idpIds)`, which returns the Active ones. Branches 2a and 3a follow spec section 7.
  - The comparison table rows are style, budget, location, property type, category and designer, each with a "View Details" link.
- **US-12 is exact to `docs/design/use-cases/US-12`:**
  - `HomePage` (the existing public home boundary class becomes `HomePage` if it isn't already) has `displayRecommendedIDPs()`, `displayPopularIDPs()` and `displayMessage()`.
  - `ViewRecommendedIDPsController.getRecommendedIDPs(userId)` → `IDPEntity.getRecommendedIDPs(userId)`. If that's empty and the user has no history, it calls `IDPEntity.getPopularIDPs()`, following the diagram.
  - Shown to logged-in customers on `/`, above the style gallery. Visitors see "Featured Designs" (6 featured IDPs, read via a plain `IDPEntity.getFeaturedIDPs()` call in `HomePage`).
- Append `"US-12"` and `"US-13"`.

**Tests:** every `alt` branch for both, ranking order, already-saved IDPs excluded, the session limit of 3.

### Task 6: Account self-service (US-05 diagrammed, US-07, US-08)

**Branch:** `feature/account-self-service`

**Do:**
- Create `app/boundary/email_service.py` (`EmailService`) as in spec section 5.
- **US-05 is exact to `docs/design/use-cases/US-05`:**
  - `ResetPasswordPage` has `displayForgotPasswordForm()`, `displayResetForm()`, `displayMessage()` and `displayResetSuccess()`.
  - `ResetPasswordController` has `requestPasswordReset(email)`, `resetPassword(token, newPassword)`, `sendResetLink(email)` (private) and `validatePassword(newPassword)` (private).
  - `UserAccountEntity` has `requestPasswordReset(email)` and `resetPassword(token, newPassword)`.
  - Token rules are in spec section 7. `sendResetLink` emails `/reset-password/<token>` through `EmailService.sendEmail`.
  - The confirm-password field is checked in `validatePassword` together with the password rules (9b).
  - Add a "Forgot password?" link on the login page.
- US-07: `MyAccountPage` (`/account`, any role) → `UpdateAccountDetailsController.updateAccountDetails(userId, name, email, phone)`, with the existing validation rules and a unique email. For designers, the page also shows the weekly summary toggle → `UpdateAccountDetailsController.setWeeklySummaryOptIn(userId, optIn)`.
- US-08: `POST /account/delete` (after typing the username to confirm) → `DeleteAccountController.deleteAccount(userId, password)`. It anonymises name, email, phone and username, sets `isAnonymised` and logs out. Reviews and enquiries keep their rows, but show "Deleted user".
- Append `"US-05"`.

**Tests:** every US-05 branch (unknown email sends nothing but shows the same message, expired token, reused token, invalid password, success), the email captured in log mode, plus US-07 and US-08.

### Task 7: Admin user accounts, unlock and lockout (US-20 to US-25, US-33)

**Branch:** `feature/admin-accounts`

**Do:**
- `ManageUserAccountsPage` (`/admin/accounts`): search by keyword (username, name or email), profile and status (US-25), with the "Export CSV" button placeholder (wired up in Task 9).
- `UserAccountFormPage` for create (US-20) and update (US-22).
- View page (US-21), and Suspend (US-23) and Reactivate (US-24) actions.
- Controllers named as in spec section 6. Methods: `createUserAccount(...)`, `getUserAccount(userId)`, `updateUserAccount(...)`, `suspendUserAccount(userId, adminId)`, `reactivateUserAccount(userId, adminId)`, `searchUserAccounts(keyword, profile, status)`.
- `UserAccountEntity.searchUserAccounts(keyword, profile, status)` is the exact signature from US-34, reused here.
- Lockout: 5 consecutive failed logins set `lockedUntil` to 15 minutes ahead (`LoginController` and entity). The login message is "This account is locked. Try again later or contact an administrator."
- US-33: `UnlockUserAccountController.unlockUserAccount(userId, adminId)` clears the lock and the failed count.
- Every change writes an `AuditLogEntity` row: action, targetType "user_account", targetId, adminId and a details text.

**Tests:** each story, admins can't suspend themselves, the lockout after 5 failures, unlock, and audit rows written.

### Task 8: Admin user profiles (US-26 to US-31)

**Branch:** `feature/admin-profiles`

**Do:**
- `ManageUserProfilesPage` and `UserProfileFormPage`, with controllers as in spec section 6.
- Methods: `createUserProfile`, `getUserProfile`, `updateUserProfile`, `suspendUserProfile`, `reactivateUserProfile` and `searchUserProfiles(keyword, role, status)`.
- The view shows the role and the number of accounts.
- Suspending a profile blocks login for its accounts (this already exists through `canLogIn`).
- Audit rows use targetType "user_profile".

**Tests:** each story, the account count, suspended-profile login blocked, audit rows.

### Task 9: Audit log and CSV export (US-32, US-34, both diagrammed)

**Branch:** `feature/audit-export`

**Do:**
- **US-32 is exact:**
  - `AuditLogPage` (`/admin/audit-log`) has `displayAuditLog()` and `displayMessage()`.
  - `ViewAuditLogController.getAuditLogs(startDate, endDate)` → `AuditLogEntity.getAuditLogs(startDate, endDate)`, newest first.
  - Validate the date range (4a) in the controller before calling the entity, following the diagram's `alt`.
  - Show the date and time, the admin's name, the action and the target.
- **US-34 is exact:**
  - `ManageUserAccountsPage.downloadCSV()` and `displayMessage()`.
  - `ExportUserAccountsController.exportUserAccountsCSV(keyword, profile, status)` → `UserAccountEntity.searchUserAccounts(...)`, then `generateCSV(accounts)` (private) if any were found.
  - File name and columns are in spec section 7. Responds with `text/csv` as an attachment.
- Add "Audit log" to the admin home tools.
- Append `"US-32"` and `"US-34"`.

**Tests:** all branches, the CSV content and headers, passwords absent, and the filters applied.

### Task 10: Company info (US-35, US-36, US-37)

**Branch:** `feature/company-info`

**Do:**
- `CompanyInfoPage` (`/designer/company`): create if none exists, otherwise view with an edit form.
- Controllers: `createCompanyInfo(designerId, ...)`, `getCompanyInfo(designerId)` and `updateCompanyInfo(designerId, ...)`.
- Validation: name required; email, phone and website formats checked.

**Tests:** create, view, update, validation, and only one record per designer.

### Task 11: Portfolio, Add IDP and manage own IDPs (US-38 diagrammed with US-45, US-39 to US-42)

**Branch:** `feature/portfolio`

**Do:**
- **US-38 is exact:**
  - `MyPortfolioPage` (`/designer/portfolio`; the form is at `/designer/portfolio/new`) has `displayAddIDPForm()`, `displaySuccess()` and `displayMessage()`.
  - `AddIDPController.addIDP(idp, photos)` calls `validateIDP(idp, photos)` (private), then `IDPEntity.addIDP(idp, photos)`.
  - `idp` is a plain dict of the form fields.
  - `photos` is a list of Werkzeug `FileStorage`. Photos are saved to `instance/uploads/` with a random filename and served at `/uploads/<filename>`. `photoUrls` stores those URLs.
  - Rules 6a, 6b and 6c are in spec section 7. Company info is required first: show a message linking to `/designer/company`.
  - Records an `idp_added` activity.
- US-42: `MyPortfolioPage` lists the designer's IDPs (all statuses except Removed), searched through `SearchMyIDPsController.searchMyIDPs(designerId, keyword)`.
- US-39: `MyIDPDetailsPage` (`/designer/portfolio/<idpId>`) → `ViewMyIDPController.getMyIDP(designerId, idpId)`.
- US-40: `EditIDPPage` → `UpdateIDPController.updateIDP(designerId, idpId, idp, photos)`. Photos can be added or removed, keeping at least one.
- US-41: `DeleteIDPController.deleteIDP(designerId, idpId)` sets status Removed, clears `isFeatured` and hides the IDP everywhere public.
- Append `"US-38"`.

**Tests:** each `alt` branch of US-38, including real file uploads in the test client (a small generated PNG; a .gif rejected; more than 5 MB rejected), ownership checks (403 for another designer's IDP), and the edit and delete flows.

### Task 12: View count, shortlist count and dashboard (US-43 diagrammed, US-44, US-46)

**Branch:** `feature/idp-interest`

**Do:**
- **US-43 is exact:**
  - `MyIDPDetailsPage` has `displayViewCount()` and `displayNoViews()`.
  - `ViewIDPViewCountController.getViewCount(idpId)` → `IDPEntity.getViewCount(idpId)`.
  - Show "<n> views", or "0 views".
- US-44: `ViewIDPShortlistCountController.getShortlistCount(idpId)` → `IDPEntity.getShortlistCount(idpId)`, shown on the same page.
- US-46: `InterestDashboardPage` (`/designer/dashboard`) → `ViewInterestDashboardController.getInterestDashboard(designerId)`. It shows views and shortlists per style and per category across the designer's portfolio as accessible bar lists (HTML/CSS bars with numbers), plus their top 5 IDPs.
- Append `"US-43"`.

**Tests:** counts shown, the zero branch, dashboard aggregation.

### Task 13: Weekly summary email (US-48 diagrammed)

**Branch:** `feature/weekly-summary`

**Do:**
- **US-48 is exact:**
  - `WeeklySummaryScheduler.triggerWeeklySummary()` («boundary», `app/boundary/weekly_summary_scheduler.py`).
  - `SendWeeklySummaryController` with `emailService` and `entity`. Methods: `sendWeeklySummaries()`, `composeSummary(summary)`, `composeNoActivityNotice()` and `scheduleRetry(designerId)`, the last three private.
  - `IDPEntity.getOptedInDesigners()` and `IDPEntity.getWeeklyStats(designerId) -> Summary`.
  - `EmailService.sendSummaryEmail(email, content)`.
  - Loop and branches follow the diagram: for each opted-in Active designer, get the stats, compose the summary or the no-activity notice, send, and call `scheduleRetry(designerId)` if sending fails. Retry up to 3 times within the run.
- Add the CLI command `send-weekly-summaries`.
- Add `POST /internal/weekly-summary`, which needs the header `X-Summary-Token` to equal the env `WEEKLY_SUMMARY_TOKEN`. If the env var is unset, the endpoint is disabled with a 404.
- Add `.github/workflows/weekly-summary.yml` with `on: schedule: cron "0 1 * * 1"` plus `workflow_dispatch`. It curls the Render endpoint using the secrets `RENDER_APP_URL` and `WEEKLY_SUMMARY_TOKEN`, and skips with a notice if they're not set.
- Append `"US-48"`.

**Tests:** opted-out designers skipped, the no-activity notice, top 3 by views, the retry path (EmailService stub failing twice then succeeding), the endpoint token check.

### Task 14: Categories, search and reports (US-49 to US-54 with US-54 diagrammed, US-55 to US-57, US-59, US-56 diagrammed)

**Branch:** `feature/categories-reports`

**Do:**
- US-49–53: `ManageCategoriesPage` and `CategoryFormPage`. Controllers `createCategory`, `getCategory` (the view shows idpCount), `updateCategory`, `suspendCategory` and `reactivateCategory`. Names must be unique.
- **US-54 is exact:** `ManageCategoriesPage.displayCategories()` and `displayMessage()`. `SearchCategoriesController.searchCategories(keyword, status)` → `CategoryEntity.searchCategories(keyword, status)`.
- **US-56 is exact:**
  - `ReportsPage` has `displayReport()`, `displayMessage()` and `displayEmptyReport()`.
  - `GenerateMonthlyReportController.generateMonthlyReport(month, year)` checks for a future month (2a, following the diagram's `alt`), then calls `PlatformActivityEntity.generateMonthlyReport(month, year) -> Report`, which includes the previous-month comparison. Figures are in spec section 7.
- US-55: `GenerateDailyReportController.generateDailyReport(date)`, against the previous day.
- US-59: `GenerateCustomReportController.generateCustomReport(startDate, endDate)`, against the same-length previous period.
- Both of those use `PlatformActivityEntity.generateReport(startDate, endDate)` internally.
- US-57: `ExportReportPDFController.exportReportPDF(reportType, params) -> bytes` builds a one-page PDF with fpdf2. Downloaded as `activity_report_<period>.pdf`.
- Append `"US-54"` and `"US-56"`.

**Tests:** CRUD with unique names, search branches, report figures against seeded fixtures (computed explicitly), the future month, the empty month, the PDF starting with `%PDF`.

### Task 15: Reported IDPs and Featured IDPs (US-58, US-60 diagrammed)

**Branch:** `feature/moderation-featured`

**Do:**
- US-58: `ReportedIDPsPage` (`/platform/reported`) lists Open flags with the IDP and reason → `ViewReportedIDPsController.getOpenReports()`.
- `ResolveReportedIDPController.resolveReport(flagId, managerId, decision)`, where decision ∈ uphold, dismiss. Uphold sets the IDP status to Removed and clears `isFeatured`. Records `reviewedBy` and `reviewedAt`.
- **US-60 is exact:**
  - `ManageFeaturedIDPsPage` (`/platform/featured`) has `displayFeaturedIDPs()`, `displaySuccess()` and `displayMessage()`.
  - `FeatureIDPController.featureIDP(idpId)` calls `countFeaturedIDPs()`, then `setFeatured(idpId, True)` if `count < 6`. `unfeatureIDP(idpId)` calls `setFeatured(idpId, False)`.
  - `IDPEntity.setFeatured` returns False for an IDP that isn't Active (5a) and sets `featuredDate` when featuring.
  - The page lists Active IDPs with search, and shows the 6 current featured slots.
- Append `"US-60"`.

**Tests:** all branches of both, and that the home page "Featured Designs" reflects changes.

### Task 16: Role homes, navigation, traceability and README

**Branch:** `feature/wrap-up`

**Do:**
- Every tool in `role_tools.py` becomes Available, linking to its page. Remove the "Coming in Sprint N" statuses; they no longer apply. Update the role home tests.
- `_nav.html` per role:
  - Customer: Browse, Favourites, Compare (n), Enquiries, Account.
  - Designer: Portfolio, Dashboard, Enquiries, Company, Account.
  - Admin: Accounts, Profiles, Audit log.
  - Manager: Categories, Reports, Reported, Featured.
  - Keep the mobile layout working: collapse the extra links behind a simple `<details>` menu under 44rem.
- `docs/design/traceability.md`: for each of the 12 diagrammed use cases, a table of diagram element → `file:line`, covering every class, attribute and method. Generate it with a small script `scripts/traceability.py` (committed) that uses the conformance parser and `inspect`.
- README: the full feature list, demo logins, how to run the weekly summary and how to set `MAIL_*` and `WEEKLY_SUMMARY_TOKEN`.
- Confirm `CONFORMING_USE_CASES` lists all 12.

**Tests:** all role pages render, every nav link resolves, the conformance test covers all 12.

---

## Final review

A whole-branch review (most capable model) against the spec and the diagrams. Then fix, re-review, and verify on the live Render site with all four demo accounts.
