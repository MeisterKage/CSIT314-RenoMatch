from sqlalchemy import event

from app.entity.db import db, utcnow


class AuditLogEntity(db.Model):
    """A record of an admin changing an account or profile. Read-only after insert."""

    __tablename__ = "audit_log"

    logId = db.Column("id", db.Integer, primary_key=True)
    adminId = db.Column(
        "admin_id", db.Integer, db.ForeignKey("user_account.id"), nullable=False, index=True
    )
    action = db.Column(db.String(50), nullable=False)
    targetType = db.Column("target_type", db.String(30), nullable=False)
    targetId = db.Column("target_id", db.Integer, nullable=False)
    details = db.Column(db.String(255), nullable=False, default="")
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    admin = db.relationship("UserAccountEntity")

    @classmethod
    def recordAction(
        cls, adminId: int, action: str, targetType: str, targetId: int, details: str = ""
    ) -> "AuditLogEntity":
        """Write one audit row for an admin change."""
        row = cls(
            adminId=adminId,
            action=action,
            targetType=targetType,
            targetId=targetId,
            details=details[:255],
        )
        db.session.add(row)
        db.session.commit()
        return row


@event.listens_for(AuditLogEntity, "before_update")
@event.listens_for(AuditLogEntity, "before_delete")
def _refuse_changes(mapper, connection, target):
    raise ValueError("Audit log records are read-only after insert.")
