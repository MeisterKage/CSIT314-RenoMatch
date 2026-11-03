from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask.views import MethodView

from app.boundary.auth_guard import role_required
from app.control.remove_favourite_controller import RemoveFavouriteController
from app.control.search_favourites_controller import SearchFavouritesController
from app.control.view_favourites_controller import ViewFavouritesController

bp = Blueprint("favourites", __name__)


class FavouritesPage(MethodView):
    """Boundary for US-15 (view), US-16 (remove) and US-17 (search) favourites.

    Each favourite is a photo card with its note. A note is edited by saving again, which
    posts to IDPDetailsPage.
    """

    decorators = [role_required("customer")]

    def __init__(self):
        self.controller = ViewFavouritesController()
        self.removeController = RemoveFavouriteController()
        self.searchController = SearchFavouritesController()

    def get(self):
        userId = g.current_account.userId
        keyword = request.args.get("keyword", "").strip()
        if keyword:
            favourites = self.searchController.searchFavourites(userId, keyword)
        else:
            favourites = self.controller.getFavourites(userId)
        return self.displayFavourites(favourites, keyword)

    def post(self, idpId):
        removed = self.removeController.removeFavourite(g.current_account.userId, idpId)
        return self.displayMessage(removed)

    def displayFavourites(self, favourites, keyword):
        return render_template("favourites/favourites.html", favourites=favourites, keyword=keyword)

    def displayMessage(self, removed):
        if removed:
            flash("Removed from your favourites.", "success")
        return redirect(url_for("favourites.favourites"))


bp.add_url_rule("/favourites", view_func=FavouritesPage.as_view("favourites"), methods=["GET"])
bp.add_url_rule(
    "/favourites/<int:idpId>/remove",
    view_func=FavouritesPage.as_view("remove_favourite"),
    methods=["POST"],
)
