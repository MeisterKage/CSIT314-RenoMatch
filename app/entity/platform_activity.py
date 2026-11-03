from datetime import date, datetime, time, timedelta

from app.entity.db import db, utcnow
from app.entity.reports import Report

ACTIVITY_TYPES = ("view", "shortlist", "register", "enquiry", "review", "idp_added")


class PlatformActivityEntity(db.Model):
    """One event on the platform, kept for counts and reports. Never deleted.

    userId is empty for an anonymous view. idpId is empty for activity that is not
    about one IDP, such as a registration or a review.
    """

    __tablename__ = "platform_activity"

    activityId = db.Column("id", db.Integer, primary_key=True)
    activityType = db.Column("activity_type", db.String(20), nullable=False, index=True)
    userId = db.Column("user_id", db.Integer, db.ForeignKey("user_account.id"), nullable=True)
    idpId = db.Column("idp_id", db.Integer, db.ForeignKey("idp.id"), nullable=True, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    @classmethod
    def recordActivity(cls, activityType: str, userId: int | None = None, idpId: int | None = None):
        """Add one activity row now and commit it."""
        row = cls(activityType=activityType, userId=userId, idpId=idpId)
        db.session.add(row)
        db.session.commit()
        return row

    @classmethod
    def countActivity(cls, startDate: date, endDate: date) -> Report:
        """The figures for the days startDate to endDate inclusive, with no comparison."""
        from app.entity.user_account import UserAccountEntity
        from app.entity.user_profile import UserProfileEntity

        start = datetime.combine(startDate, time.min)
        end = datetime.combine(endDate + timedelta(days=1), time.min)

        def count(activityType: str) -> int:
            return (
                db.session.query(cls)
                .filter(cls.activityType == activityType)
                .filter(cls.timestamp >= start, cls.timestamp < end)
                .count()
            )

        newDesigners = (
            db.session.query(cls)
            .join(UserAccountEntity, UserAccountEntity.userId == cls.userId)
            .join(UserProfileEntity, UserProfileEntity.profileId == UserAccountEntity.profileId)
            .filter(cls.activityType == "register", UserProfileEntity.roleType == "designer")
            .filter(cls.timestamp >= start, cls.timestamp < end)
            .count()
        )
        return Report(
            reportType="custom",
            startDate=startDate,
            endDate=endDate,
            newUsers=count("register"),
            newDesigners=newDesigners,
            newIDPs=count("idp_added"),
            idpViews=count("view"),
            shortlists=count("shortlist"),
            enquiries=count("enquiry"),
        )

    @classmethod
    def generateReport(cls, startDate: date, endDate: date) -> Report:
        """US-55 and US-59: the figures for a day range, compared with the previous period of
        the same length that ends the day before it starts."""
        report = cls.countActivity(startDate, endDate)
        previousEnd = startDate - timedelta(days=1)
        previousStart = previousEnd - (endDate - startDate)
        report.previous = cls.countActivity(previousStart, previousEnd)
        return report

    @classmethod
    def generateMonthlyReport(cls, month: int, year: int) -> Report:
        """US-56 1.1.1: the figures for one calendar month, compared with the month before."""
        startDate = date(year, month, 1)
        endDate = date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)
        previousEnd = startDate - timedelta(days=1)
        report = cls.countActivity(startDate, endDate)
        report.reportType = "monthly"
        report.previous = cls.countActivity(previousEnd.replace(day=1), previousEnd)
        report.previous.reportType = "monthly"
        return report
