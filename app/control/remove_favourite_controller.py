from app.entity import FavouriteEntity


class RemoveFavouriteController:
    """US-16: remove a favourite."""

    def __init__(self):
        self.entity = FavouriteEntity

    def removeFavourite(self, userId: int, idpId: int):
        return self.entity.removeFavourite(userId, idpId)
