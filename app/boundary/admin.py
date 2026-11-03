from datetime import datetime

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.boundary.role_tools import CHANGE_PASSWORD, Tool
from app.control.create_user_account_controller import CreateUserAccountController
from app.control.errors import ValidationError
from app.control.export_user_accounts_controller import ExportUserAccountsController
from app.control.create_user_profile_controller import CreateUserProfileController
from app.control.reactivate_user_account_controller import ReactivateUserAccountController
from app.control.reactivate_user_profile_controller import ReactivateUserProfileController
from app.control.search_user_accounts_controller import SearchUserAccountsController
from app.control.search_user_profiles_controller import SearchUserProfilesController
from app.control.suspend_user_account_controller import SuspendUserAccountController
from app.control.suspend_user_profile_controller import SuspendUserProfileController
from app.control.unlock_user_account_controller import UnlockUserAccountController
from app.control.update_user_account_controller import UpdateUserAccountController
from app.control.update_user_profile_controller import UpdateUserProfileController
from app.control.view_user_account_controller import ViewUserAccountController
from app.control.view_user_profile_controller import ViewUserProfileController
from app.entity.user_profile import ROLE_TYPES

bp = Blueprint("admin", __name__, url_prefix="/admin")

TOOLS = [
    Tool(
        "User accounts",
        "Create, view, update, suspend and search accounts.",
        sprint=1,
        endpoint="admin.accounts",
    ),
    Tool(
        "User profiles",
        "Group accounts by role and suspend a whole role at once.",
        sprint=1,
        endpoint="admin.profiles",
    ),
    Tool(
        "Audit log",
        "See which admin changed which account, and when.",
        sprint=4,
        endpoint="audit_log.audit_log",
    ),
    Tool("Failed logins", "Spot repeated failed logins and unlock genuine users.", sprint=4),
    Tool(
        "Export accounts",
        "Download the account list as a CSV file.",
        sprint=4,
        endpoint="admin.accounts",
    ),
    CHANGE_PASSWORD,
]

NO_ACCOUNTS_TO_EXPORT = "No accounts to export."
PAGE_SIZE = 25
STATUS_FILTERS = ("Active", "Suspended")


class AdminHomePage(MethodView):
    decorators = [role_required("admin")]

    def get(self):
        return render_template("role_home.html", role_label="User Admin", tools=TOOLS)


def safeNext(default: str, prefix: str = "/admin/accounts") -> str:
    """The page to return to after an action: a path under `prefix`, else `default`."""
    target = request.form.get("next", "")
    if target.startswith(prefix) and "//" not in target and "\\" not in target:
        return target
    return default


class ManageUserAccountsPage(MethodView):
    """Boundary for US-21 (view), US-23 (suspend), US-24 (reactivate), US-25 (search) and
    US-33 (unlock), and for US-34 (export CSV). `controller` is the US-34 class diagram's
    ExportUserAccountsController, so the other controllers use their own attribute names.
    `displayMessage` takes no argument, as in the US-34 class diagram, so what it shows is
    held in `message`, `category` and `nextUrl`. `csvFile` holds the file for `downloadCSV`."""

    decorators = [role_required("admin")]

    def __init__(self):
        self.controller = ExportUserAccountsController()
        self.message = None
        self.category = "success"
        self.nextUrl = None
        self.csvFile = None
        self.searchController = SearchUserAccountsController()
        self.viewController = ViewUserAccountController()
        self.suspendController = SuspendUserAccountController()
        self.reactivateController = ReactivateUserAccountController()
        self.unlockController = UnlockUserAccountController()

    def get(self, userId=None):
        if request.endpoint == "admin.accounts_export":
            return self.exportAccounts()
        if userId is None:
            return self.displayAccounts()
        return self.displayAccount(userId)

    def post(self, userId):
        actions = {
            "admin.account_suspend": self.suspendController.suspendUserAccount,
            "admin.account_reactivate": self.reactivateController.reactivateUserAccount,
            "admin.account_unlock": self.unlockController.unlockUserAccount,
        }
        messages = {
            "admin.account_suspend": "Account suspended.",
            "admin.account_reactivate": "Account reactivated.",
            "admin.account_unlock": "Account unlocked.",
        }
        endpoint = request.endpoint
        try:
            actions[endpoint](userId, g.current_account.userId)
        except ValidationError as error:
            self.message, self.category = str(error), "danger"
            return self.displayMessage()
        self.message, self.category = messages[endpoint], "success"
        return self.displayMessage()

    def exportAccounts(self):
        """US-34 step 1: click "Export CSV", which sends the current search filters."""
        keyword, profile, status = self.searchFilters()
        self.csvFile = self.controller.exportUserAccountsCSV(keyword, profile, status)  # 1.1
        if self.csvFile:  # [accounts not empty]
            return self.downloadCSV()  # 1.2
        self.message, self.category = NO_ACCOUNTS_TO_EXPORT, "info"  # [3a. no accounts found]
        self.nextUrl = url_for("admin.accounts", **self.filterArgs(keyword, profile, status))
        return self.displayMessage()  # 1.3

    def downloadCSV(self):
        filename = f"user_accounts_{datetime.now().strftime('%Y-%m-%d')}.csv"
        return Response(
            self.csvFile,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @staticmethod
    def searchFilters():
        keyword = request.args.get("keyword", "").strip()
        profile = request.args.get("profile", "").strip()
        status = request.args.get("status", "").strip()
        if status not in STATUS_FILTERS:
            status = ""
        return keyword, profile, status

    @staticmethod
    def filterArgs(keyword, profile, status):
        filters = {"keyword": keyword, "profile": profile, "status": status}
        return {key: value for key, value in filters.items() if value}

    def displayAccounts(self):
        keyword, profile, status = self.searchFilters()
        accounts = self.searchController.searchUserAccounts(keyword, profile, status)
        try:
            page = max(1, int(request.args.get("page", "1")))
        except ValueError:
            page = 1
        pages = max(1, -(-len(accounts) // PAGE_SIZE))
        page = min(page, pages)
        filters = {"keyword": keyword, "profile": profile, "status": status}
        return render_template(
            "admin/accounts.html",
            accounts=accounts[(page - 1) * PAGE_SIZE : page * PAGE_SIZE],
            total=len(accounts),
            page=page,
            pages=pages,
            filters=filters,
            pageArgs=self.filterArgs(keyword, profile, status),
            profiles=self.searchController.getProfiles(),
            statuses=STATUS_FILTERS,
        )

    def displayAccount(self, userId):
        account = self.viewController.getUserAccount(userId)
        if account is None:
            abort(404)
        return render_template("admin/account_view.html", account=account)

    def displayMessage(self):
        flash(self.message, self.category)
        return redirect(self.nextUrl or safeNext(url_for("admin.accounts")))


class UserAccountFormPage(MethodView):
    """Boundary for US-20 (create) and US-22 (update)."""

    decorators = [role_required("admin")]

    FIELDS = ("username", "name", "email", "phone", "profileId")

    def __init__(self):
        self.createController = CreateUserAccountController()
        self.updateController = UpdateUserAccountController()
        self.viewController = ViewUserAccountController()
        self.searchController = SearchUserAccountsController()

    def get(self, userId=None):
        if userId is None:
            return self.displayForm(None, {"profileId": ""}, {})
        account = self.viewController.getUserAccount(userId)
        if account is None:
            abort(404)
        form = {
            "name": account.name,
            "email": account.email,
            "phone": account.phone,
            "profileId": account.profileId,
        }
        return self.displayForm(account, form, {})

    def post(self, userId=None):
        form = {field: request.form.get(field, "") for field in self.FIELDS}
        form["profileId"] = self.profileNumber(form["profileId"])
        adminId = g.current_account.userId
        if userId is None:
            try:
                account = self.createController.createUserAccount(
                    username=form["username"],
                    email=form["email"],
                    password=request.form.get("password", ""),
                    name=form["name"],
                    profileId=form["profileId"],
                    phone=form["phone"],
                    adminId=adminId,
                )
            except ValidationError as error:
                return self.displayForm(None, form, error.errors)
            return self.displayMessage("Account created.", account.userId)
        account = self.viewController.getUserAccount(userId)
        if account is None:
            abort(404)
        try:
            self.updateController.updateUserAccount(
                userId,
                name=form["name"],
                email=form["email"],
                phone=form["phone"],
                profileId=form["profileId"],
                adminId=adminId,
            )
        except ValidationError as error:
            return self.displayForm(account, form, error.errors)
        return self.displayMessage("Account updated.", userId)

    @staticmethod
    def profileNumber(value: str):
        return int(value) if value.isdigit() else None

    def displayForm(self, account, form, errors):
        return render_template(
            "admin/account_form.html",
            account=account,
            form=form,
            errors=errors,
            profiles=self.searchController.getProfiles(),
        )

    def displayMessage(self, message, userId):
        flash(message, "success")
        return redirect(url_for("admin.account_view", userId=userId))


class ManageUserProfilesPage(MethodView):
    """Boundary for US-27 (view), US-29 (suspend), US-30 (reactivate) and US-31 (search).
    `displayMessage` takes no argument, so what it shows is held in `message`, `category`."""

    decorators = [role_required("admin")]

    def __init__(self):
        self.searchController = SearchUserProfilesController()
        self.viewController = ViewUserProfileController()
        self.suspendController = SuspendUserProfileController()
        self.reactivateController = ReactivateUserProfileController()
        self.message = None
        self.category = "success"

    def get(self, profileId=None):
        if profileId is None:
            return self.displayProfiles()
        return self.displayProfile(profileId)

    def post(self, profileId):
        if request.endpoint == "admin.profile_suspend":
            action, done = self.suspendController.suspendUserProfile, "Profile suspended."
        else:
            action, done = self.reactivateController.reactivateUserProfile, "Profile reactivated."
        try:
            action(profileId, g.current_account.userId)
        except ValidationError as error:
            self.message, self.category = str(error), "danger"
            return self.displayMessage()
        self.message, self.category = done, "success"
        return self.displayMessage()

    def displayProfiles(self):
        keyword = request.args.get("keyword", "").strip()
        role = request.args.get("role", "").strip()
        status = request.args.get("status", "").strip()
        if role not in self.searchController.roleTypes:
            role = ""
        if status not in self.searchController.statuses:
            status = ""
        filters = {"keyword": keyword, "role": role, "status": status}
        return render_template(
            "admin/profiles.html",
            profiles=self.searchController.searchUserProfiles(keyword, role, status),
            filters=filters,
            hasFilters=any(filters.values()),
            roleTypes=self.searchController.roleTypes,
            statuses=self.searchController.statuses,
        )

    def displayProfile(self, profileId):
        profile = self.viewController.getUserProfile(profileId)
        if profile is None:
            abort(404)
        return render_template("admin/profile_view.html", profile=profile)

    def displayMessage(self):
        flash(self.message, self.category)
        return redirect(safeNext(url_for("admin.profiles"), "/admin/profiles"))


class UserProfileFormPage(MethodView):
    """Boundary for US-26 (create) and US-28 (update)."""

    decorators = [role_required("admin")]

    def __init__(self):
        self.createController = CreateUserProfileController()
        self.updateController = UpdateUserProfileController()
        self.viewController = ViewUserProfileController()

    def get(self, profileId=None):
        if profileId is None:
            return self.displayForm(None, {"roleType": ""}, {})
        profile = self.viewController.getUserProfile(profileId)
        if profile is None:
            abort(404)
        form = {"name": profile.name, "description": profile.description}
        return self.displayForm(profile, form, {})

    def post(self, profileId=None):
        form = {
            "name": request.form.get("name", ""),
            "description": request.form.get("description", ""),
            "roleType": request.form.get("roleType", ""),
        }
        adminId = g.current_account.userId
        if profileId is None:
            try:
                profile = self.createController.createUserProfile(
                    form["name"], form["description"], form["roleType"], adminId
                )
            except ValidationError as error:
                return self.displayForm(None, form, error.errors)
            return self.displayMessage("Profile created.", profile.profileId)
        profile = self.viewController.getUserProfile(profileId)
        if profile is None:
            abort(404)
        try:
            self.updateController.updateUserProfile(
                profileId, form["name"], form["description"], adminId
            )
        except ValidationError as error:
            return self.displayForm(profile, form, error.errors)
        return self.displayMessage("Profile updated.", profileId)

    def displayForm(self, profile, form, errors):
        return render_template(
            "admin/profile_form.html",
            profile=profile,
            form=form,
            errors=errors,
            roleTypes=ROLE_TYPES,
        )

    def displayMessage(self, message, profileId):
        flash(message, "success")
        return redirect(url_for("admin.profile_view", profileId=profileId))


bp.add_url_rule("/", view_func=AdminHomePage.as_view("home"))
bp.add_url_rule("/accounts", view_func=ManageUserAccountsPage.as_view("accounts"))
bp.add_url_rule("/accounts/export", view_func=ManageUserAccountsPage.as_view("accounts_export"))
bp.add_url_rule(
    "/accounts/new", view_func=UserAccountFormPage.as_view("account_new"), methods=["GET", "POST"]
)
bp.add_url_rule("/accounts/<int:userId>", view_func=ManageUserAccountsPage.as_view("account_view"))
bp.add_url_rule(
    "/accounts/<int:userId>/edit",
    view_func=UserAccountFormPage.as_view("account_edit"),
    methods=["GET", "POST"],
)
for action in ("suspend", "reactivate", "unlock"):
    bp.add_url_rule(
        f"/accounts/<int:userId>/{action}",
        view_func=ManageUserAccountsPage.as_view(f"account_{action}"),
        methods=["POST"],
    )
bp.add_url_rule("/profiles", view_func=ManageUserProfilesPage.as_view("profiles"))
bp.add_url_rule(
    "/profiles/new", view_func=UserProfileFormPage.as_view("profile_new"), methods=["GET", "POST"]
)
bp.add_url_rule(
    "/profiles/<int:profileId>", view_func=ManageUserProfilesPage.as_view("profile_view")
)
bp.add_url_rule(
    "/profiles/<int:profileId>/edit",
    view_func=UserProfileFormPage.as_view("profile_edit"),
    methods=["GET", "POST"],
)
for action in ("suspend", "reactivate"):
    bp.add_url_rule(
        f"/profiles/<int:profileId>/{action}",
        view_func=ManageUserProfilesPage.as_view(f"profile_{action}"),
        methods=["POST"],
    )
