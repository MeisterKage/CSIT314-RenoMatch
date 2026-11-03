# US-13 diagram text (extracted from US-13_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-13 Class Diagram
[box] «boundary» | CompareIDPPage
[box] - controller: CompareIDPsController
[box] + displayComparison(): void | + displayMessage(): void
[box] «control» | CompareIDPsController
[box] - entity: IDPEntity
[box] + compareIDPs(idpIds: int[]): IDP[]
[box] «entity» | IDPEntity
[box] - idpId: int | - title: String | - style: String | - budget: float | - location: String | - propertyType: String
[box] + compareIDPs(idpIds: int[]): IDP[]
=== US-13 Sequence Diagram
[box] Registered User
[box] : CompareIDPPage
[box] : CompareIDPsController
[box] : IDPEntity
[box] opt
[box] alt
[box] opt
[box] [1a. 3 IDPs already selected]
[box] [2 to 3 IDPs selected]
[box] [2a. fewer than 2 IDPs selected]
[box] [3a. a selected IDP is no longer available]
[edge] 1: tick "Compare" on an IDP
[box] 1.1: displayMessage()
[edge] 2: click "Compare"
[edge] 2.1: compareIDPs(idpIds)
[edge] 2.1.1: compareIDPs(idpIds)
[edge] idps
[edge] idps
[box] 2.2: displayComparison()
[box] 2.3: displayMessage()
[edge] null
[box] 2.4: displayMessage()
```
