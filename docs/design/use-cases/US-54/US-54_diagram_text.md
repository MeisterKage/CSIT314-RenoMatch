# US-54 diagram text (extracted from US-54_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-54 Class Diagram
[box] «boundary» | ManageCategoriesPage
[box] - controller: SearchCategoriesController
[box] + displayCategories(): void | + displayMessage(): void
[box] «control» | SearchCategoriesController
[box] - entity: CategoryEntity
[box] + searchCategories(keyword: String, status: String): Category[]
[box] «entity» | CategoryEntity
[box] - categoryId: int | - name: String | - description: String | - status: String | - idpCount: int
[box] + searchCategories(keyword: String, status: String): Category[]
=== US-54 Sequence Diagram
[box] Platform Manager
[box] : ManageCategoriesPage
[box] : SearchCategoriesController
[box] : CategoryEntity
[box] alt
[box] [categories not empty]
[box] [3a. no category found]
[edge] 1: enter keyword, click "Search"
[edge] 1.1: searchCategories(keyword, status)
[edge] 1.1.1: searchCategories(keyword, status)
[edge] categories
[edge] categories
[box] 1.2: displayCategories()
[box] 1.3: displayMessage()
```
