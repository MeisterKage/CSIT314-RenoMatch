# US-43 diagram text (extracted from US-43_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-43 Class Diagram
[box] «boundary» | MyIDPDetailsPage
[box] - controller: ViewIDPViewCountController
[box] + displayViewCount(): void | + displayNoViews(): void
[box] «control» | ViewIDPViewCountController
[box] - entity: IDPEntity
[box] + getViewCount(idpId: int): int
[box] «entity» | IDPEntity
[box] - idpId: int | - designerId: int | - title: String | - viewCount: int
[box] + getViewCount(idpId: int): int
=== US-43 Sequence Diagram
[box] Interior Designer
[box] : MyIDPDetailsPage
[box] : ViewIDPViewCountController
[box] : IDPEntity
[box] alt
[box] [viewCount > 0]
[box] [2a. not viewed yet]
[edge] 1: select IDP
[edge] 1.1: getViewCount(idpId)
[edge] 1.1.1: getViewCount(idpId)
[edge] viewCount
[edge] viewCount
[box] 1.2: displayViewCount()
[box] 1.3: displayNoViews()
```
