from flask import Blueprint, current_app, flash, redirect, send_from_directory, url_for

bp = Blueprint("uploads", __name__)


@bp.get("/uploads/<filename>")
def uploaded_file(filename):
    """Serve a saved IDP photo. send_from_directory refuses any path outside the folder."""
    response = send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.app_errorhandler(413)
def upload_too_large(error):
    """The whole request is over MAX_CONTENT_LENGTH (30 MB): ask for fewer or smaller photos."""
    flash(
        "Your photos are too large. Keep each under 5 MB and the whole upload under 30 MB.",
        "danger",
    )
    return redirect(url_for("portfolio.portfolio"))
