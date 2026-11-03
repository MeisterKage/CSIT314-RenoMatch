from app.entity import FavouriteEntity


class ViewFavouritesController:
    """US-15: list the user's favourites."""

    def __init__(self):
        self.entity = FavouriteEntity

    def getFavourites(self, userId: int):
        return self.entity.getFavourites(userId)

    def getFavourite(self, userId: int, idpId: int):
        """The user's favourite for one IDP, or None. Used to pre-fill the save form."""
        return self.entity.getFavourite(userId, idpId)
