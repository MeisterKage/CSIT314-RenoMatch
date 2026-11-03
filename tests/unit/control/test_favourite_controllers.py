"""US-14, US-15, US-16, US-17: favourite controllers."""

from app.control.remove_favourite_controller import RemoveFavouriteController
from app.control.save_favourite_controller import SaveFavouriteController
from app.control.search_favourites_controller import SearchFavouritesController
from app.control.view_favourites_controller import ViewFavouritesController
from app.entity import FavouriteEntity


def test_controllers_hold_the_entity_class():
    for controller in (
        SaveFavouriteController,
        ViewFavouritesController,
        RemoveFavouriteController,
        SearchFavouritesController,
    ):
        assert controller().entity is FavouriteEntity


def test_save_view_search_remove_flow(make_idp, make_account):
    user, idp = make_account(), make_idp(title="Calm study")
    assert SaveFavouriteController().saveFavourite(user.userId, idp.idpId, "nice").note == "nice"
    assert len(ViewFavouritesController().getFavourites(user.userId)) == 1
    assert len(SearchFavouritesController().searchFavourites(user.userId, "calm")) == 1
    assert len(SearchFavouritesController().searchFavourites(user.userId, "zzz")) == 0
    assert RemoveFavouriteController().removeFavourite(user.userId, idp.idpId) is True
    assert ViewFavouritesController().getFavourites(user.userId) == []
