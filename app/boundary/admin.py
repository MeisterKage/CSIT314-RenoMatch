from flask import (
    Blueprint,
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
from app.control.reactivate_user_account_controller import ReactivateUserAccountController
from app.control.search_user_accounts_controller import SearchUserAccountsController
from app.control.suspend_user_account_controller import SuspendUserAccountController
from app.control.unlock_user_account_controller import UnlockUserAccountController
from app.control.update_user_account_controller import UpdateUserAccountController
from app.control.view_user_account_controller import ViewUserAccountController

bp = Blueprint("admin", __name__, url_prefix="/admin")

TOOLS = [
    Tool(
        "User accounts",
        "Create, view, update, suspend and search accounts.",
        sprint=1,
        endpoint="admin.accounts",
    ),
    Tool("User profiles", "Group accounts by role and suspend a whole role at once.", sprint=1),
    Tool("Audit log", "See which admin changed which account, and when.", sprint=4),
    Tool("Failed logins", "Spot repeated failed logins and unlock genuine users.", sprint=4),
    Tool("Export accounts", "Download the account list as a CSV file.", sprint=4),
    CHANGE_PASSWORD,
]

PAGE_SIZE = 25
STATUS_FILTERS = ("Active", "Suspended")


class AdminHomePage(MethodView):
    decorators = [role_required("admin")]

    def get(self):
        return render_template("role_home.html", role_label="User Admin", tools=TOOLS)


def safeNext(default: str) -> str:
    """The page to return to after an action: a path under /admin/accounts, else `default`."""
    target = request.form.get("next", "")
    if target.startswith("/admin/accounts") and "//" not in target and "\\" not in target:
        return target
    return default


class ManageUserAccountsPage(MethodView):
    """Boundary for US-21 (view), US-23 (suspend), US-24 (reactivate), US-25 (search) and
    US-33 (unlock). The Export CSV button is a placeholder until US-34 is wired up. The
    `controller` attribute of the US-34 class diagram (ExportUserAccountsController) is left
    free for that use case, so the controllers here use their own attribute names."""

    decorators = [role_required("admin")]

    def __init__(self):
        self.searchController = SearchUserAccountsController()
        self.viewController = ViewUserAccountController()
        self.suspendController = SuspendUserAccountController()
        self.reactivateController = ReactivateUserAccountController()
        self.unlockController = UnlockUserAccountController()

    def get(self, userId=None):
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
            return self.displayMessage(str(error), "danger")
        return self.displayMessage(messages[endpoint], "success")

    def displayAccounts(self):
        keyword = request.args.get("keyword", "").strip()
        profile = request.args.get("profile", "").strip()
        status = request.args.get("status", "").strip()
        if status not in STATUS_FILTERS:
            status = ""
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
            pageArgs={key: value for key, value in filters.items() if value},
            profiles=self.searchController.getProfiles(),
            statuses=STATUS_FILTERS,
        )

    def displayAccount(self, userId):
        account = self.viewController.getUserAccount(userId)
        if account is None:
            abort(404)
        return render_template("admin/account_view.html", account=account)

    def displayMessage(self, message, category):
        flash(message, category)
        return redirect(safeNext(url_for("admin.accounts")))


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


bp.add_url_rule("/", view_func=AdminHomePage.as_view("home"))
bp.add_url_rule("/accounts", view_func=ManageUserAccountsPage.as_view("accounts"))
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
