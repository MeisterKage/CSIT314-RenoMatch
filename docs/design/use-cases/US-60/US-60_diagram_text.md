# US-60 diagram text (extracted from US-60_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-60 Class Diagram
[box] «boundary» | ManageFeaturedIDPsPage
[box] - controller: FeatureIDPController
[box] + displayFeaturedIDPs(): void | + displaySuccess(): void | + displayMessage(): void
[box] «control» | FeatureIDPController
[box] - entity: IDPEntity
[box] + featureIDP(idpId: int): boolean | + unfeatureIDP(idpId: int): boolean
[box] «entity» | IDPEntity
[box] - idpId: int | - designerId: int | - title: String | - status: String | - isFeatured: boolean | - featuredDate: Date
[box] + countFeaturedIDPs(): int | + setFeatured(idpId: int, featured: boolean): boolean
=== US-60 Sequence Diagram
[box] Platform Manager
[box] : ManageFeaturedIDPsPage
[box] : FeatureIDPController
[box] : IDPEntity
[box] alt
[box] opt
[box] alt
[box] [count < 6]
[box] [4a. 6 IDPs already featured]
[box] [3a. unfeature a featured IDP]
[box] [result = true]
[box] [5a. IDP suspended or removed]
[edge] 1: select IDP, click "Feature"
[edge] 1.1: featureIDP(idpId)
[edge] 1.1.1: countFeaturedIDPs()
[edge] count
[edge] 1.1.2: setFeatured(idpId, true)
[edge] result
[edge] result
[box] 1.2: displaySuccess()
[box] 1.3: displayMessage()
[edge] false
[box] 1.4: displayMessage()
[edge] 2: click "Unfeature"
[edge] 2.1: unfeatureIDP(idpId)
[edge] 2.1.1: setFeatured(idpId, false)
[edge] true
[edge] true
[box] 2.2: displaySuccess()
```
