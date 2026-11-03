from app.entity import FavouriteEntity


class SearchFavouritesController:
    """US-17: search the user's favourites by keyword."""

    def __init__(self):
        self.entity = FavouriteEntity

    def searchFavourites(self, userId: int, keyword: str | None):
        return self.entity.searchFavourites(userId, keyword)
