from app.entity.db import db, utcnow


class CompanyInfo(db.Model):
    __tablename__ = "company_info"

    id = db.Column(db.Integer, primary_key=True)
    designer_id = db.Column(
        db.Integer, db.ForeignKey("user_account.id"), unique=True, nullable=False
    )
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    address = db.Column(db.String(255), nullable=False, default="")
    phone = db.Column(db.String(20), nullable=False, default="")
    email = db.Column(db.String(120), nullable=False, default="")
    website = db.Column(db.String(200), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    designer = db.relationship("UserAccount")
