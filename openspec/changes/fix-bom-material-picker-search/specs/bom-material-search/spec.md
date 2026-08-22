## ADDED Requirements

### Requirement: BOM material picker supports search
The BOM material picker in the MaterialDetail page SHALL provide a search input that allows the user to filter materials by name or code via server-side search.

#### Scenario: User searches for a material
- **WHEN** user opens the BOM material picker and types a keyword in the search bar
- **THEN** the picker SHALL call the materials API with the keyword and display only matching results (excluding the current product)

### Requirement: BOM material picker displays search results with details
The BOM material picker SHALL display each search result with its thumbnail, name, code, and current stock quantity.

#### Scenario: Search results show material details
- **WHEN** search results are loaded
- **THEN** each result item SHALL show the material's thumbnail (or placeholder), name, code label, and current stock number

### Requirement: BOM material picker auto-loads on open
The BOM material picker SHALL automatically load the full material list (excluding the current product) when the picker popup is opened.

#### Scenario: Picker opens with material list
- **WHEN** user clicks "添加" on the BOM section
- **THEN** the material picker popup opens and displays the loaded list of available materials
