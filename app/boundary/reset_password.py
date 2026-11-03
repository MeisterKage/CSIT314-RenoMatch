from flask import Blueprint, render_template, request
from flask.views import MethodView

from app.control.reset_password_controller import (
    EXPIRED_MESSAGE,
    SENT_MESSAGE,
    ResetPasswordController,
)

bp = Blueprint("reset_password", __name__)

MISMATCH = "Passwords do not match."


class ResetPasswordPage(MethodView):
    """Boundary for US-05. `post` on /forgot-password is sequence step 1 (1.1, then 1.2 or
    1.3 displayMessage). `post` on /reset-password/<token> is step 2 (2.1, then 2.2
    displayResetSuccess, or 2.3 / 2.4 displayMessage). The display methods take no argument,
    as in the class diagram, so what they show is held in `message` and `token`."""

    def __init__(self):
        self.controller = ResetPasswordController()
        self.message = None
        self.token = None

    def get(self, token=None):
        if token is None:
            return self.displayForgotPasswordForm()
        self.token = token
        return self.displayResetForm()

    def post(self, token=None):
        if token is None:
            return self.sendLink()
        return self.setNewPassword(token)

    def sendLink(self):
        self.controller.requestPasswordReset(request.form.get("email", ""))
        # 1.2 (email registered) and 1.3 (not registered) show the same message.
        self.message = SENT_MESSAGE
        return self.displayMessage()

    def setNewPassword(self, token):
        password = request.form.get("newPassword", "")
        mismatch = password != request.form.get("confirmPassword", "")
        # validatePassword takes only newPassword, so a mismatch is passed as an empty
        # password, which breaks the rules (9b).
        result = self.controller.resetPassword(token, "" if mismatch else password)
        self.token = token
        if result:
            return self.displayResetSuccess()  # 2.2
        self.message = MISMATCH if mismatch else self.controller.message
        return self.displayMessage()  # 2.3 (token invalid or expired) or 2.4 (9b)

    def displayForgotPasswordForm(self):
        return render_template("auth/forgot_password.html", form={}, errors={}, message=None)

    def displayResetForm(self):
        return render_template(
            "auth/reset_password.html", form={}, errors={}, token=self.token, message=None
        )

    def displayMessage(self):
        """1.2, 1.3, 2.3 and 2.4: `message`. After a failed new password the form is shown
        again; after an invalid or expired link, a link to request a new one."""
        if request.endpoint == "reset_password.forgot":
            return render_template(
                "auth/forgot_password.html", form={}, errors={}, message=self.message
            )
        return render_template(
            "auth/reset_password.html",
            form={},
            errors={},
            token=self.token,
            message=self.message,
            expired=self.message == EXPIRED_MESSAGE,
        )

    def displayResetSuccess(self):
        return render_template("auth/reset_success.html")


bp.add_url_rule("/forgot-password", view_func=ResetPasswordPage.as_view("forgot"))
bp.add_url_rule("/reset-password/<token>", view_func=ResetPasswordPage.as_view("reset"))
