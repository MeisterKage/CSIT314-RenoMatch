# US-34 diagram text (extracted from US-34_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-34 Class Diagram
[box] «boundary» | ManageUserAccountsPage
[box] - controller: ExportUserAccountsController
[box] + downloadCSV(): void | + displayMessage(): void
[box] «control» | ExportUserAccountsController
[box] - entity: UserAccountEntity
[box] + exportUserAccountsCSV(keyword: String, profile: String, status: String): File | - generateCSV(accounts: UserAccount[]): File
[box] «entity» | UserAccountEntity
[box] - userId: int | - name: String | - email: String | - profileId: int | - status: String | - createdAt: DateTime
[box] + searchUserAccounts(keyword: String, profile: String, status: String): UserAccount[]
=== US-34 Sequence Diagram
[box] Administrator
[box] : ManageUserAccountsPage
[box] : ExportUserAccountsController
[box] : UserAccountEntity
[box] alt
[box] [accounts not empty]
[box] [3a. no accounts found]
[edge] 1: click "Export CSV"
[edge] 1.1: exportUserAccountsCSV(keyword, profile, status)
[edge] 1.1.1: searchUserAccounts(keyword, profile, status)
[edge] accounts
[box] 1.1.2: generateCSV(accounts)
[edge] csvFile
[box] 1.2: downloadCSV()
[edge] null
[box] 1.3: displayMessage()
```
