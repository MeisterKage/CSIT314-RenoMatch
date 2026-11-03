# US-32 diagram text (extracted from US-32_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-32 Class Diagram
[box] «boundary» | AuditLogPage
[box] - controller: ViewAuditLogController
[box] + displayAuditLog(): void | + displayMessage(): void
[box] «control» | ViewAuditLogController
[box] - entity: AuditLogEntity
[box] + getAuditLogs(startDate: Date, endDate: Date): AuditLog[]
[box] «entity» | AuditLogEntity
[box] - logId: int | - adminId: int | - action: String | - targetType: String | - targetId: int | - timestamp: DateTime
[box] + getAuditLogs(startDate: Date, endDate: Date): AuditLog[]
=== US-32 Sequence Diagram
[box] Administrator
[box] : AuditLogPage
[box] : ViewAuditLogController
[box] : AuditLogEntity
[box] alt
[box] alt
[box] [valid date range]
[box] [4a. start date after end date]
[box] [logs not empty]
[box] [2a. no records found]
[edge] 1: open "Audit Log", set date range
[edge] 1.1: getAuditLogs(startDate, endDate)
[edge] 1.1.1: getAuditLogs(startDate, endDate)
[edge] logs
[edge] logs
[box] 1.2: displayAuditLog()
[box] 1.3: displayMessage()
[edge] null
[box] 1.4: displayMessage()
```
