from functools import wraps

from flask import abort, g, redirect, session, url_for

from app.control.login_controller import LoginController

ROLE_HOME = {
    "admin": "admin.home",
    "designer": "public.home",
    "customer": "public.home",
    "platform": "public.home",
}


def load_current_account() -> None:
    """Before every request: set g.current_account, dropping sessions that are no longer valid."""
    g.current_account = None
    account_id = session.get("account_id")
    if account_id is None:
        return
    account = LoginController().get_active_account(account_id)
    if account is None:
        session.clear()
        return
    g.current_account = account


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            account = g.get("current_account")
            if account is None:
                return redirect(url_for("auth.login"))
            if account.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


login_required = role_required(*ROLE_HOME)
