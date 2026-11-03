from app.entity import IDPEntity


class ViewIDPDetailsController:
    """US-10: open an IDP's public details and count the view."""

    def __init__(self):
        self.entity = IDPEntity

    def viewIDPDetails(self, idpId: int, viewerId: int | None) -> IDPEntity | None:
        """The Active IDP, or None when it is missing, Suspended or Removed."""
        return self.entity.recordView(idpId, viewerId)
