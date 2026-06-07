## ADDED Requirements

### Requirement: Guided four-step workflow for production orders
The system SHALL present the in-production order detail page as a four-step guided workflow: check materials → confirm yield → upload product image → complete.

#### Scenario: Step 1 - material checking active
- **WHEN** user views an in-production order where not all materials are checked
- **THEN** the material list shows unchecked items with pulse dot animation, subsequent steps are locked

#### Scenario: Step 2 - yield confirmation active
- **WHEN** all materials are checked but yield not confirmed
- **THEN** yield confirmation input appears with pulse dot

#### Scenario: Step 3 - product image upload active
- **WHEN** yield is confirmed but product image not uploaded
- **THEN** product image upload card appears with pulse dot

#### Scenario: Step 4 - complete active
- **WHEN** all materials checked, yield confirmed, and product image uploaded
- **THEN** complete button is enabled with pulse dot

### Requirement: Separate cards for materials and product image
The system SHALL display material checking, yield confirmation, and product image upload as separate cards.

#### Scenario: Three separate cards
- **WHEN** user views an in-production order
- **THEN** material list, yield confirmation, and product image upload are displayed as independent cards

### Requirement: Pulse dot animation
The system SHALL use pulse dot animation on the next actionable step.

#### Scenario: Pulse dot on next step
- **WHEN** a workflow step is the next actionable item
- **THEN** a pulsing dot indicator appears on that step's card

### Requirement: Collapsible material list
The system SHALL allow the material list to be collapsed and expanded.

#### Scenario: Toggle collapse
- **WHEN** user taps the material list card header
- **THEN** the list toggles between expanded and collapsed
