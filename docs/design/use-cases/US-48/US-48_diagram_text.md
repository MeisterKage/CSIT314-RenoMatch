# US-48 diagram text (extracted from US-48_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-48 Class Diagram
[box] «boundary» | WeeklySummaryScheduler
[box] - controller: SendWeeklySummaryController
[box] + triggerWeeklySummary(): void
[box] «control» | SendWeeklySummaryController
[box] - emailService: EmailService | - entity: IDPEntity
[box] + sendWeeklySummaries(): void | - composeSummary(summary: Summary): String | - composeNoActivityNotice(): String | - scheduleRetry(designerId: int): void
[box] «entity» | IDPEntity
[box] - idpId: int | - designerId: int | - viewCount: int | - shortlistCount: int
[box] + getOptedInDesigners(): Designer[] | + getWeeklyStats(designerId: int): Summary
[box] «boundary» | EmailService
[box] + sendSummaryEmail(email: String, content: String): boolean
=== US-48 Sequence Diagram
[box] System Scheduler
[box] : WeeklySummaryScheduler
[box] : SendWeeklySummaryController
[box] : IDPEntity
[box] : EmailService
[box] Interior Designer
[box] loop
[box] alt
[box] opt
[box] [for each opted-in designer]
[box] [summary has activity]
[box] [3a. no activity this week]
[box] [5a. sent = false]
[edge] 1: triggerWeeklySummary()
[edge] 1.1: sendWeeklySummaries()
[edge] 1.1.1: getOptedInDesigners()
[edge] designers
[edge] 1.1.2: getWeeklyStats(designerId)
[edge] summary
[box] 1.1.3: composeSummary(summary)
[box] 1.1.4: composeNoActivityNotice()
[edge] 1.1.5: sendSummaryEmail(email, content)
[edge] 1.1.5.1: weekly summary email
[edge] sent
[box] 1.1.6: scheduleRetry(designerId)
```
