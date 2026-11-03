from app.entity import IDPEntity


class CompareIDPsController:
    """US-13: look up the selected IDPs for the comparison table."""

    def __init__(self):
        self.entity = IDPEntity

    def compareIDPs(self, idpIds: list[int]) -> list[IDPEntity]:
        """Sequence 2.1: the Active IDPs among idpIds, from IDPEntity.compareIDPs (2.1.1)."""
        return self.entity.compareIDPs(idpIds)
