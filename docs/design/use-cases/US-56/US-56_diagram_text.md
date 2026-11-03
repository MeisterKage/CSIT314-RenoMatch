# US-56 diagram text (extracted from US-56_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-56 Class Diagram
[box] «boundary» | ReportsPage
[box] - controller: GenerateMonthlyReportController
[box] + displayReport(): void | + displayMessage(): void | + displayEmptyReport(): void
[box] «control» | GenerateMonthlyReportController
[box] - entity: PlatformActivityEntity
[box] + generateMonthlyReport(month: int, year: int): Report
[box] «entity» | PlatformActivityEntity
[box] - activityId: int | - activityType: String | - userId: int | - idpId: int | - timestamp: DateTime
[box] + generateMonthlyReport(month: int, year: int): Report
=== US-56 Sequence Diagram
[box] Platform Manager
[box] : ReportsPage
[box] : GenerateMonthlyReportController
[box] : PlatformActivityEntity
[box] alt
[box] alt
[box] [month not in the future]
[box] [2a. future month selected]
[box] [activity recorded]
[box] [3a. no activity this month]
[edge] 1: select month and year, click "Generate"
[edge] 1.1: generateMonthlyReport(month, year)
[edge] 1.1.1: generateMonthlyReport(month, year)
[edge] report
[edge] report
[box] 1.2: displayReport()
[box] 1.3: displayEmptyReport()
[edge] null
[box] 1.4: displayMessage()
```
