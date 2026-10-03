from app.entity.db import db


class IDPPhoto(db.Model):
    __tablename__ = "idp_photo"

    id = db.Column(db.Integer, primary_key=True)
    idp_id = db.Column(db.Integer, db.ForeignKey("idp.id"), nullable=False, index=True)
    content_type = db.Column(db.String(50), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    caption = db.Column(db.String(120), nullable=False, default="")
    position = db.Column(db.Integer, nullable=False, default=0)

    idp = db.relationship("IDP", back_populates="photos")
