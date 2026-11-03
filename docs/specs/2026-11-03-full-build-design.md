# RenoMatch Full Build — Design Spec

**Date:** 2026-11-03
**Deadline:** final submission 12 Nov 2026, 23:59
**Status:** Agreed with Shawn on 3 Nov 2026

## 1. Goal

Build all 60 user stories in the Final Report on the RenoMatch website, so that:

1. **The 12 diagrammed use cases match their diagrams exactly.** These are US-05, US-12, US-13, US-19, US-32, US-34, US-38, US-43, US-48, US-54, US-56 and US-60, defined in the team's diagram files under `docs/design/use-cases/US-xx/`. The code uses the same class names, attribute names, method names, parameter names and capitalisation, the same call order, and the same `alt`/`opt` branches as the sequence diagrams.
2. **The other 48 stories follow the same conventions**, so the whole codebase reads as one design.

The sources of truth, in order:
- `docs/design/use-cases/US-xx/US-xx_diagrams.drawio`, with its text extract `US-xx_diagram_text.md`
- the `US-xx_1_Use_Case_Description.png` files, for messages and business rules
- this spec

This spec replaces the user-story numbering in `2026-10-03-renovation-platform-design.md`. Use the Final Report's US-01 to US-60 numbering everywhere: code docstrings, tests and commit messages.

## 2. Naming conventions (binding)

| Element | Rule | Example |
|---|---|---|
| Entity class | `<Name>Entity` | `UserAccountEntity`, `IDPEntity` |
| Entity attribute | camelCase, exactly as in the diagrams; the DB column can keep its old snake_case name through `db.Column("old_name", ...)` | `userId = db.Column("id", db.Integer, primary_key=True)` |
| Controller class | `<Verb><Noun>Controller`, or the exact diagram name | `ResetPasswordController` |
| Boundary class | `<Name>Page`, or the exact diagram name; a Flask `MethodView` | `ResetPasswordPage` |
| Methods (all layers) | camelCase, exactly as in the diagrams | `requestPasswordReset(email)` |
| Parameters | camelCase, exactly as in the diagrams | `newPassword`, `idpIds`, `designerId` |
| Private methods (`-` in the diagrams) | exact diagram name with **no** leading underscore; the docstring starts with `Private:` | `def validatePassword(self, newPassword):` |
| Boundary → controller link | `self.controller = <Controller>()` set in `__init__` | matches `- controller: ResetPasswordController` |
| Controller → entity link | `self.entity = <Entity>` (the class) set in `__init__`; entity methods are classmethods | matches `- entity: UserAccountEntity` |
| Display methods | boundary methods named `display...()` return the rendered response | `displayResetSuccess()` |
| Return types | `boolean` → `bool`; `X[]` → `list[XEntity]`; `File` → `bytes` plus a filename; `Report`/`Summary` → dataclasses in `app/entity/reports.py` | |

Python style (ruff `E`, `F`) still applies. camelCase names are deliberate; don't "fix" them to snake_case.

Each diagrammed controller method must make **the same entity calls in the same order** as its sequence diagram, guarded by the diagram's conditions. A test per diagram asserts the observable result of each `alt` branch.

## 3. Entity model

All entities live in `app/entity/`, one module per entity. Text status values use these exact strings:

- accounts: `"Active"`, `"Suspended"`
- profiles: `"Active"`, `"Suspended"`
- categories: `"Active"`, `"Suspended"`
- IDPs: `"Active"`, `"Suspended"`, `"Removed"`
- flags: `"Open"`, `"Upheld"`, `"Dismissed"`

| Entity (table) | Attributes (camelCase) | Notes |
|---|---|---|
| `UserProfileEntity` (`user_profile`) | profileId, name, description, roleType, status | roleType ∈ admin, designer, customer, platform |
| `UserAccountEntity` (`user_account`) | userId, username, name, email, phone, passwordHash, profileId, status, failedLogins, lockedUntil, resetToken, tokenExpiry, weeklySummaryOptIn, isAnonymised, createdAt | `role` property comes from the profile. `resetToken` is stored hashed. `weeklySummaryOptIn` defaults to True. Usernames and emails are stored lowercase. |
| `LoginAttemptEntity` (`login_attempt`) | attemptId, username, userId, success, attemptedAt | |
| `CompanyInfoEntity` (`company_info`) | companyId, designerId, name, description, address, phone, email, website, createdAt, updatedAt | one per designer |
| `CategoryEntity` (`category`) | categoryId, name, description, status, idpCount | `idpCount` is a read-only property: the number of Active IDPs in the category |
| `IDPEntity` (`idp`) | idpId, designerId, categoryId, title, description, style, propertyType, budget, location, photoUrls, stage, status, isFeatured, featuredDate, viewCount, shortlistCount, completedOn, createdAt | `budget` is a float. `photoUrls` is a JSON list of URL strings. `stage` ∈ Current, Past. `viewCount` and `shortlistCount` are stored counters. |
| `FavouriteEntity` (`favourite`) | favouriteId, userId, idpId, note, savedAt | unique (userId, idpId) |
| `PlatformActivityEntity` (`platform_activity`) | activityId, activityType, userId, idpId, timestamp | activityType ∈ view, shortlist, register, enquiry, review, idp_added |
| `EnquiryEntity` (`enquiry`) | enquiryId, userId, designerId, idpId, subject, createdAt | userId is the customer |
| `EnquiryMessageEntity` (`enquiry_message`) | messageId, enquiryId, senderId, body, sentAt | |
| `ReviewEntity` (`review`) | reviewId, designerId, userId, rating, comment, createdAt | rating 1–5, comment ≤ 1000 characters, one review per (designerId, userId) |
| `IDPFlagEntity` (`idp_flag`) | flagId, idpId, reporterId, reason, status, reviewedBy, reviewedAt, createdAt | |
| `AuditLogEntity` (`audit_log`) | logId, adminId, action, targetType, targetId, details, timestamp | read-only after insert |

Removed: `PasswordResetToken`, `IDPPhoto`, `ViewEvent` and `ShortlistEvent`. They are replaced by `UserAccountEntity.resetToken/tokenExpiry`, `IDPEntity.photoUrls`, and `PlatformActivityEntity` with `IDPEntity.viewCount/shortlistCount`.

**Counting rules:**
- Opening an IDP's public details page (US-10) adds a `view` activity and increments `viewCount`. Views by the IDP's own designer are not counted (US-43).
- Saving a favourite (US-14) adds a `shortlist` activity and increments `shortlistCount`. Removing a favourite does not decrement it.

Transient report classes live in `app/entity/reports.py`: `Report` (monthly, daily and custom-range figures with previous-period comparison) and `Summary` (weekly designer stats).

There are no migrations. Schema changes need `flask --app app seed --reset` locally, and Render rebuilds the database on every start.

## 4. Seed data

`app/seed.py` keeps 100+ rows per main entity and fills every new attribute:
- `photoUrls` uses 1–3 images from `app/boundary/static/img/idp/idp-01.jpg` … `idp-32.jpg`, chosen deterministically.
- `viewCount` and `shortlistCount` equal the number of matching `PlatformActivityEntity` rows.
- About 8,000 view activities and 1,500 shortlist activities spread over 90 days, plus register, enquiry and review activities.
- Exactly 6 IDPs have `isFeatured` set, with a `featuredDate`.
- About 10% of designers have `weeklySummaryOptIn` turned off.
- Accounts are mostly Active, about 4% Suspended. Categories are 95% Active. IDPs are 92% Active, 4% Suspended and 4% Removed (Removed when their flag is Upheld).
- Demo logins are unchanged: admin, manager, designer and customer, all with password `Password123!`.

## 5. Email and scheduling

- `app/boundary/email_service.py`: class `EmailService` («boundary» in US-48). It has `sendSummaryEmail(email, content) -> bool` and `sendEmail(email, subject, body) -> bool`. It sends through SMTP when `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` and `MAIL_SENDER` are configured. Otherwise it writes the email to the application log and returns True. Tests use the log mode and check the captured log.
- US-48 scheduling: `WeeklySummaryScheduler.triggerWeeklySummary()` («boundary») is called from two places. One is the CLI command `flask --app app send-weekly-summaries`. The other is `POST /internal/weekly-summary`, protected by the `WEEKLY_SUMMARY_TOKEN` header token, which is called by a scheduled GitHub Actions workflow every Monday at 01:00 UTC (09:00 Singapore time).

## 6. Story map

All boundaries require the right role, except the visitor pages. Every admin action that changes an account or profile writes an `AuditLogEntity` row.

| Story | Actor | Page (boundary) | Controller | Route |
|---|---|---|---|---|
| US-01 Browse IDPs as a visitor | Visitor | `BrowseIDPsPage` | `BrowseIDPsController` | `/idps` |
| US-02 Register | Visitor | `RegisterPage` (exists) | `RegisterController` | `/register` |
| US-03 Log in | Registered user | `LoginPage` | `LoginController` | `/login` |
| US-04 Log out | Registered user | `LogoutAction` | `LogoutController` | `/logout` |
| **US-05 Reset password** | Registered user | **`ResetPasswordPage`** | **`ResetPasswordController`** | `/forgot-password`, `/reset-password/<token>` |
| US-06 Change password | Registered user | `ChangePasswordPage` (exists) | `ChangePasswordController` | `/account/password` |
| US-07 Update own details | Registered user | `MyAccountPage` | `UpdateAccountDetailsController` | `/account` |
| US-08 Delete own account | Registered user | `MyAccountPage` | `DeleteAccountController` | `POST /account/delete` |
| US-09 Search IDPs | Registered user | `BrowseIDPsPage` | `SearchIDPsController` | `/idps?keyword=&category=&style=&propertyType=&minBudget=&maxBudget=` |
| US-10 View IDP details | Registered user | `IDPDetailsPage` | `ViewIDPDetailsController` | `/idps/<idpId>` |
| US-11 View designer profile | Registered user | `DesignerProfilePage` | `ViewDesignerProfileController` | `/designers/<designerId>` |
| **US-12 Recommended IDPs** | Registered user | **`HomePage`** | **`ViewRecommendedIDPsController`** | `/` (customers logged in) |
| **US-13 Compare IDPs** | Registered user | **`CompareIDPPage`** | **`CompareIDPsController`** | `/compare` (selection kept in session) |
| US-14 Save favourite | Registered user | `IDPDetailsPage` | `SaveFavouriteController` | `POST /idps/<idpId>/favourite` |
| US-15 View favourites | Registered user | `FavouritesPage` | `ViewFavouritesController` | `/favourites` |
| US-16 Remove favourite | Registered user | `FavouritesPage` | `RemoveFavouriteController` | `POST /favourites/<idpId>/remove` |
| US-17 Search favourites | Registered user | `FavouritesPage` | `SearchFavouritesController` | `/favourites?keyword=` |
| US-18 Send enquiry | Registered user | `IDPDetailsPage` | `SendEnquiryController` | `POST /idps/<idpId>/enquiry` |
| **US-19 Review designer** | Registered user | **`DesignerProfilePage`** | **`RateReviewDesignerController`** | `/designers/<designerId>/review` |
| US-20–25 Manage user accounts | Administrator | `ManageUserAccountsPage`, `UserAccountFormPage` | `CreateUserAccountController`, `ViewUserAccountController`, `UpdateUserAccountController`, `SuspendUserAccountController`, `ReactivateUserAccountController`, `SearchUserAccountsController` | `/admin/accounts...` |
| US-26–31 Manage user profiles | Administrator | `ManageUserProfilesPage`, `UserProfileFormPage` | `CreateUserProfileController`, `ViewUserProfileController`, `UpdateUserProfileController`, `SuspendUserProfileController`, `ReactivateUserProfileController`, `SearchUserProfilesController` | `/admin/profiles...` |
| **US-32 Audit log** | Administrator | **`AuditLogPage`** | **`ViewAuditLogController`** | `/admin/audit-log` |
| US-33 Unlock account | Administrator | `ManageUserAccountsPage` | `UnlockUserAccountController` | `POST /admin/accounts/<userId>/unlock` |
| **US-34 Export CSV** | Administrator | **`ManageUserAccountsPage`** | **`ExportUserAccountsController`** | `/admin/accounts/export` |
| US-35–37 Company info | Interior designer | `CompanyInfoPage` | `CreateCompanyInfoController`, `ViewCompanyInfoController`, `UpdateCompanyInfoController` | `/designer/company` |
| **US-38 Add IDP** (includes US-45 photos) | Interior designer | **`MyPortfolioPage`** | **`AddIDPController`** | `/designer/portfolio`, `/designer/portfolio/new` |
| US-39 View own IDP | Interior designer | `MyIDPDetailsPage` | `ViewMyIDPController` | `/designer/portfolio/<idpId>` |
| US-40 Update IDP | Interior designer | `EditIDPPage` | `UpdateIDPController` | `/designer/portfolio/<idpId>/edit` |
| US-41 Delete IDP | Interior designer | `MyIDPDetailsPage` | `DeleteIDPController` | `POST /designer/portfolio/<idpId>/delete` (sets status Removed) |
| US-42 Search own IDPs | Interior designer | `MyPortfolioPage` | `SearchMyIDPsController` | `/designer/portfolio?keyword=` |
| **US-43 View count** | Interior designer | **`MyIDPDetailsPage`** | **`ViewIDPViewCountController`** | on `/designer/portfolio/<idpId>` |
| US-44 Shortlist count | Interior designer | `MyIDPDetailsPage` | `ViewIDPShortlistCountController` | on `/designer/portfolio/<idpId>` |
| US-45 Upload photos | Interior designer | part of US-38 and US-40 | `AddIDPController` / `UpdateIDPController` | |
| US-46 Interest dashboard | Interior designer | `InterestDashboardPage` | `ViewInterestDashboardController` | `/designer/dashboard` |
| US-47 Reply to enquiries | Interior designer | `EnquiriesPage` | `ViewEnquiriesController`, `ReplyEnquiryController` | `/designer/enquiries...` |
| **US-48 Weekly email** | System scheduler | **`WeeklySummaryScheduler`**, **`EmailService`** | **`SendWeeklySummaryController`** | CLI and `/internal/weekly-summary`; opt-in toggle on `MyAccountPage` for designers |
| US-49–53 Manage categories | Platform manager | `ManageCategoriesPage`, `CategoryFormPage` | `CreateCategoryController`, `ViewCategoryController`, `UpdateCategoryController`, `SuspendCategoryController`, `ReactivateCategoryController` | `/platform/categories...` |
| **US-54 Search categories** | Platform manager | **`ManageCategoriesPage`** | **`SearchCategoriesController`** | `/platform/categories?keyword=&status=` |
| US-55 Daily report | Platform manager | `ReportsPage` | `GenerateDailyReportController` | `/platform/reports?type=daily` |
| **US-56 Monthly report** | Platform manager | **`ReportsPage`** | **`GenerateMonthlyReportController`** | `/platform/reports?type=monthly&month=&year=` |
| US-57 Export report PDF | Platform manager | `ReportsPage` | `ExportReportPDFController` | `/platform/reports/pdf?...` (fpdf2) |
| US-58 Review reported IDPs | Platform manager | `ReportedIDPsPage` | `ViewReportedIDPsController`, `ResolveReportedIDPController` | `/platform/reported` |
| US-59 Custom range report | Platform manager | `ReportsPage` | `GenerateCustomReportController` | `/platform/reports?type=custom&startDate=&endDate=` |
| **US-60 Feature IDPs** | Platform manager | **`ManageFeaturedIDPsPage`** | **`FeatureIDPController`** | `/platform/featured` |

The visitor home page shows "Featured Designs", the 6 featured IDPs (US-60). A logged-in customer's home page shows US-12 instead: "Recommended for you", with "Popular designs" or the empty message as fallbacks.

## 7. Business rules from the use case descriptions

- **US-05:**
  - The token expires after 1 hour and is single-use.
  - An unknown email shows the same "check your email" message, with no email sent (4a).
  - The password rules are those of the existing `password_problem`.
- **US-12:**
  - Recommendations come from the categories and styles of IDPs the user has viewed or saved.
  - Only Active IDPs are listed, excluding ones already saved.
  - Ranked by number of matches, then viewCount, up to 10.
  - With no history, show popular IDPs, the top 10 by viewCount, under the heading "Popular designs".
  - With history but no matches, show "No recommendations yet. Browse IDPs to get personalised suggestions".
- **US-13:**
  - Compare 2–3 IDPs.
  - Ticking a 4th shows "You can compare up to 3 IDPs".
  - Fewer than 2 shows "Select at least 2 IDPs to compare".
  - If an IDP is no longer Active, show the rest and the message "One IDP is no longer available".
  - The table shows style, budget, location, property type, category and designer.
- **US-19:**
  - `checkEligibility` returns `"eligible"`, `"not_contacted"` (shows "You can only review designers you have contacted") or `"already_reviewed"` (opens the existing review for editing).
  - The rating must be 1–5 and the comment ≤ 1000 characters.
  - The average rating is shown on the designer profile.
- **US-32:**
  - Newest first.
  - "No audit records found for this period".
  - A start date after the end date shows an error.
- **US-34:**
  - Columns: user ID, name, email, user profile, status, date created. Never passwords.
  - The file is named `user_accounts_YYYY-MM-DD.csv`.
  - It uses the current search filters.
  - No matches shows "No accounts to export".
- **US-38:**
  - Requires the designer's company info (US-35) first.
  - All fields are required, with at least one photo.
  - Photos must be JPG or PNG and ≤ 5 MB each.
  - A suspended category asks the designer to choose another.
  - Photos are saved under the instance upload folder and served from `/uploads/<file>`.
- **US-43:**
  - The page shows "<n> views".
  - With 0 views, `displayNoViews()` shows "0 views".
- **US-48:**
  - The summary covers the last 7 days: total views, total shortlists and the top 3 IDPs by views.
  - With no activity, the email says "No new activity this week" and suggests updating the portfolio.
  - If sending fails, `scheduleRetry` retries up to 3 times in the same run.
- **US-54:**
  - Searches by name containment, case-insensitive.
  - Status filter: all, Active or Suspended.
  - Shows name, status and idpCount.
  - "No categories match your search".
- **US-56:**
  - Figures: new registered users, new designers, new IDPs, IDP views, shortlists and enquiries, each against the previous month.
  - A future month shows "Please select a past or current month".
  - No activity shows all zeros and a note that there was no activity.
- **US-60:**
  - Up to 6 featured at a time; only Active IDPs.
  - A 7th shows "Maximum of 6 featured IDPs. Unfeature one first".
  - Unfeature frees the slot.
  - Featuring records `featuredDate`.

## 8. Quality bar

- Test-first for every story: a `test(US-xx)` commit comes before the `feat(US-xx)` commit.
- Each diagrammed use case gets:
  - a controller unit test per `alt` branch
  - a boundary test per page
  - a "diagram conformance" test that checks the class, attribute and method names exist with the exact spelling, read from the diagram text extract
- Merging, CI and deployment are as in Sprint 0: PR per task, merge commits, Render deploys after checks pass.
- No AI attribution anywhere.
- A traceability table at `docs/design/traceability.md` maps every diagrammed class and method to `file:line`.
