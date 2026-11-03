# US-38 diagram text (extracted from US-38_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-38 Class Diagram
[box] «boundary» | MyPortfolioPage
[box] - controller: AddIDPController
[box] + displayAddIDPForm(): void | + displaySuccess(): void | + displayMessage(): void
[box] «control» | AddIDPController
[box] - entity: IDPEntity
[box] + addIDP(idp: IDP, photos: File[]): boolean | - validateIDP(idp: IDP, photos: File[]): boolean
[box] «entity» | IDPEntity
[box] - idpId: int | - designerId: int | - title: String | - description: String | - categoryId: int | - style: String | - propertyType: String | - budget: float | - location: String | - photoUrls: String[]
[box] + addIDP(idp: IDP, photos: File[]): boolean
=== US-38 Sequence Diagram
[box] Interior Designer
[box] : MyPortfolioPage
[box] : AddIDPController
[box] : IDPEntity
[box] alt
[box] alt
[box] [details and photos valid]
[box] [6a. required fields missing]
[box] [6b. photo not JPG/PNG or over 5 MB]
[box] [result = true]
[box] [6c. category suspended]
[edge] 1: enter details, upload photos, click "Save"
[edge] 1.1: addIDP(idp, photos)
[box] 1.1.1: validateIDP(idp, photos)
[edge] 1.1.2: addIDP(idp, photos)
[edge] result
[edge] result
[box] 1.2: displaySuccess()
[box] 1.3: displayMessage()
[edge] missingFields
[box] 1.4: displayMessage()
[edge] invalidPhoto
[box] 1.5: displayMessage()
```
