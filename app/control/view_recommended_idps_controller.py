from dataclasses import dataclass

from app.entity import IDPEntity


@dataclass
class Recommendations:
    """What the home page shows: recommendedIdps, else popularIdps, else a message.

    recommendedIdps is the entity's answer to getRecommendedIDPs. popularIdps is set only
    when the user has no history (alt 2a). Both are None for alt 3a.
    """

    recommendedIdps: list[IDPEntity] | None
    popularIdps: list[IDPEntity] | None = None


class ViewRecommendedIDPsController:
    """US-12: recommended IDPs for a user, falling back to popular IDPs."""

    def __init__(self):
        self.entity = IDPEntity

    def getRecommendedIDPs(self, userId: int) -> Recommendations:
        """Sequence 1.1: getRecommendedIDPs (1.1.1), then getPopularIDPs (1.1.2) for 2a.

        The entity returns idps when there are matches, [] with no viewing or saving
        history (2a) and None when nothing matches (3a).
        """
        idps = self.entity.getRecommendedIDPs(userId)
        if idps:
            return Recommendations(idps)
        if idps is None:
            return Recommendations(None)
        return Recommendations(idps, self.entity.getPopularIDPs())
