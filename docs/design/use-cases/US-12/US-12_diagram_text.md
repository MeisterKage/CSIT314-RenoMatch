# US-12 diagram text (extracted from US-12_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-12 Class Diagram
[box] «boundary» | HomePage
[box] - controller: ViewRecommendedIDPsController
[box] + displayRecommendedIDPs(): void | + displayMessage(): void | + displayPopularIDPs(): void
[box] «control» | ViewRecommendedIDPsController
[box] - entity: IDPEntity
[box] + getRecommendedIDPs(userId: int): IDP[]
[box] «entity» | IDPEntity
[box] - idpId: int | - title: String | - categoryId: int | - style: String | - viewCount: int | - status: String
[box] + getRecommendedIDPs(userId: int): IDP[] | + getPopularIDPs(): IDP[]
=== US-12 Sequence Diagram
[box] Registered User
[box] : HomePage
[box] : ViewRecommendedIDPsController
[box] : IDPEntity
[box] alt
[box] [idps not empty]
[box] [2a. no viewing or saving history]
[box] [3a. no matching IDPs]
[edge] 1: open home page
[edge] 1.1: getRecommendedIDPs(userId)
[edge] 1.1.1: getRecommendedIDPs(userId)
[edge] idps
[edge] idps
[box] 1.2: displayRecommendedIDPs()
[edge] 1.1.2: getPopularIDPs()
[edge] popularIdps
[edge] popularIdps
[box] 1.3: displayPopularIDPs()
[edge] null
[box] 1.4: displayMessage()
```
