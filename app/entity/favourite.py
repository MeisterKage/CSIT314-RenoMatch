from sqlalchemy import or_, update
from sqlalchemy.exc import IntegrityError

from app.entity.db import db, utcnow
from app.entity.idp import IDPEntity, _publicDesigner
from app.entity.platform_activity import PlatformActivityEntity

NOTE_MAX_LENGTH = 255


class FavouriteEntity(db.Model):
    """An IDP a user has saved, with an optional note. One per (userId, idpId)."""

    __tablename__ = "favourite"
    __table_args__ = (db.UniqueConstraint("user_id", "idp_id", name="uq_favourite_user_idp"),)

    favouriteId = db.Column("id", db.Integer, primary_key=True)
    userId = db.Column(
        "user_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    idpId = db.Column("idp_id", db.Integer, db.ForeignKey("idp.id"), nullable=False)
    note = db.Column(db.String(255), nullable=False, default="")
    savedAt = db.Column("saved_at", db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("UserAccountEntity")
    idp = db.relationship("IDPEntity")

    @classmethod
    def saveFavourite(cls, userId: int, idpId: int, note: str | None) -> "FavouriteEntity | None":
        """US-14: save an Active IDP for the user, or update the note when already saved.

        A new favourite adds a `shortlist` PlatformActivityEntity and increments the IDP's
        shortlistCount in the same commit. Updating a note counts nothing. Returns None
        when the IDP does not exist, is not Active or has a hidden designer, or the note is
        over 255 characters.
        """
        note = (note or "").strip()
        if len(note) > NOTE_MAX_LENGTH:
            return None
        idp = db.session.get(IDPEntity, idpId)
        if idp is None or idp.status != "Active" or not IDPEntity._designerIsPublic(idp):
            return None
        favourite = cls.getFavourite(userId, idpId)
        if favourite is not None:
            favourite.note = note
            db.session.commit()
            return favourite
        favourite = cls(userId=userId, idpId=idpId, note=note)
        db.session.add(favourite)
        db.session.add(PlatformActivityEntity(activityType="shortlist", userId=userId, idpId=idpId))
        db.session.execute(
            update(IDPEntity)
            .where(IDPEntity.idpId == idpId)
            .values(shortlistCount=IDPEntity.shortlistCount + 1)
        )
        try:
            db.session.commit()
        except IntegrityError:
            # A concurrent save of the same IDP won the race: keep that row, update its note.
            db.session.rollback()
            favourite = cls.query.filter_by(userId=userId, idpId=idpId).one()
            favourite.note = note
            db.session.commit()
            return favourite
        db.session.refresh(idp)
        return favourite

    @classmethod
    def getFavourite(cls, userId: int, idpId: int) -> "FavouriteEntity | None":
        """The user's favourite for one IDP, or None when it is not saved."""
        return cls.query.filter_by(userId=userId, idpId=idpId).first()

    @classmethod
    def getFavourites(cls, userId: int) -> "list[FavouriteEntity]":
        """US-15: the user's favourites whose IDP is still Active, newest first."""
        return cls._activeQuery(userId).all()

    @classmethod
    def searchFavourites(cls, userId: int, keyword: str | None) -> "list[FavouriteEntity]":
        """US-17: the user's favourites matching the keyword in title, description or note."""
        query = cls._activeQuery(userId)
        if keyword and keyword.strip():
            word = keyword.strip()
            query = query.filter(
                or_(
                    IDPEntity.title.icontains(word, autoescape=True),
                    IDPEntity.description.icontains(word, autoescape=True),
                    cls.note.icontains(word, autoescape=True),
                )
            )
        return query.all()

    @classmethod
    def removeFavourite(cls, userId: int, idpId: int) -> bool:
        """US-16: delete the favourite. shortlistCount and the activity row stay as they are."""
        favourite = cls.getFavourite(userId, idpId)
        if favourite is None:
            return False
        db.session.delete(favourite)
        db.session.commit()
        return True

    @classmethod
    def _activeQuery(cls, userId: int):
        return (
            cls.query.join(IDPEntity, cls.idpId == IDPEntity.idpId)
            .filter(cls.userId == userId, IDPEntity.status == "Active", _publicDesigner())
            .order_by(cls.savedAt.desc(), cls.favouriteId.desc())
        )
