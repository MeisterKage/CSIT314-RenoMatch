import logging

from app.boundary.email_service import EmailService
from app.entity import IDPEntity
from app.entity.reports import Summary

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
NO_ACTIVITY_LINE = "No new activity this week"


class SendWeeklySummaryController:
    """US-48: email each opted-in designer their views and shortlists of the last 7 days.

    `pending` keeps the email address and content of the last send for each designer, which
    `scheduleRetry(designerId)` needs because the diagram passes it only the designerId.
    """

    def __init__(self):
        self.emailService = EmailService()
        self.entity = IDPEntity
        self.pending = {}

    def sendWeeklySummaries(self) -> None:
        """1.1: get the opted-in designers (1.1.1), then for each one (loop) get the weekly stats
        (1.1.2), compose the summary (1.1.3) when there is activity or the no-activity notice
        (1.1.4) when there is none (3a), send it (1.1.5) and schedule a retry (1.1.6) if it was
        not sent (5a)."""
        designers = self.entity.getOptedInDesigners()  # 1.1.1
        for designer in designers:  # [for each opted-in designer]
            designerId = designer.userId
            summary = self.entity.getWeeklyStats(designerId)  # 1.1.2
            if summary.hasActivity:  # [summary has activity]
                content = self.composeSummary(summary)  # 1.1.3
            else:  # [3a. no activity this week]
                content = self.composeNoActivityNotice()  # 1.1.4
            self.pending[designerId] = (designer.email, content)
            sent = self.emailService.sendSummaryEmail(designer.email, content)  # 1.1.5
            if not sent:  # [5a. sent = false]
                self.scheduleRetry(designerId)  # 1.1.6

    def composeSummary(self, summary: Summary) -> str:
        """Private: the email text for a week with activity."""
        lines = [
            f"Hi {summary.designerName or 'there'},",
            "",
            f"Here is the interest in your projects from {summary.startDate:%d %b %Y} "
            f"to {summary.endDate:%d %b %Y}.",
            "",
            f"Views: {summary.totalViews}",
            f"Shortlists: {summary.totalShortlists}",
        ]
        if summary.topIDPs:
            lines += ["", "Your top projects by views:"]
            lines += [f"{rank}. {title} ({views} views)" for rank, (title, views) in
                      enumerate(summary.topIDPs, start=1)]
        lines += ["", "The RenoMatch team"]
        return "\n".join(lines)

    def composeNoActivityNotice(self) -> str:
        """Private: the email text for a week with no views or shortlists."""
        return "\n".join(
            [
                "Hi,",
                "",
                f"{NO_ACTIVITY_LINE}. Your projects had no views or shortlists in the last 7 days.",
                "Updating your portfolio with new photos or projects is a good way to attract "
                "attention.",
                "",
                "The RenoMatch team",
            ]
        )

    def scheduleRetry(self, designerId: int) -> None:
        """Private: retry the failed send to this designer, up to 3 times in this run."""
        email, content = self.pending[designerId]
        for attempt in range(1, MAX_RETRIES + 1):
            if self.emailService.sendSummaryEmail(email, content):
                return
            logger.warning("Weekly summary retry %d of %d failed for designer %s",
                           attempt, MAX_RETRIES, designerId)
        logger.warning("Giving up on the weekly summary for designer %s", designerId)
