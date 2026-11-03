from app.entity import FavouriteEntity


class SaveFavouriteController:
    """US-14: save an IDP as a favourite, or update its note when already saved."""

    def __init__(self):
        self.entity = FavouriteEntity

    def saveFavourite(self, userId: int, idpId: int, note: str | None):
        return self.entity.saveFavourite(userId, idpId, note)
