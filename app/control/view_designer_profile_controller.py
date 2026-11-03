from dataclasses import dataclass

from app.entity import (
    CompanyInfoEntity,
    IDPEntity,
    ReviewEntity,
    UserAccountEntity,
)


@dataclass
class DesignerProfile:
    designer: UserAccountEntity
    company: CompanyInfoEntity | None
    idps: list[IDPEntity]
    averageRating: float
    reviews: list[ReviewEntity]


class ViewDesignerProfileController:
    """US-11: a designer's public profile, portfolio and reviews."""

    def __init__(self):
        self.entity = UserAccountEntity

    def viewDesignerProfile(self, designerId: int) -> DesignerProfile | None:
        """The profile, or None when designerId is not an Active designer account."""
        designer = self.entity.findById(designerId)
        if (
            designer is None
            or designer.role != "designer"
            or designer.status != "Active"
            or designer.isAnonymised
        ):
            return None
        return DesignerProfile(
            designer=designer,
            company=CompanyInfoEntity.findByDesignerId(designerId),
            idps=IDPEntity.getActiveByDesigner(designerId),
            averageRating=ReviewEntity.getAverageRating(designerId),
            reviews=ReviewEntity.getReviews(designerId),
        )
