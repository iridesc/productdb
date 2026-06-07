## ADDED Requirements

### Requirement: Guided step-by-step workflow for pending orders
The system SHALL present the pending sales order detail page as a three-step guided workflow where each step unlocks only after the previous step is completed.

#### Scenario: Step 1 active - material allocation
- **WHEN** user views a pending order where not all materials are confirmed
- **THEN** the material list is expanded by default with unconfirmed items showing a pulse dot animation, and the image upload section is locked (greyed out, non-interactive)

#### Scenario: Step 2 active - image upload
- **WHEN** user views a pending order where all materials are confirmed but images are not all uploaded
- **THEN** the material list is collapsed showing "已全部分配", the image upload section is unlocked with pulse dot animation on upload areas that are still empty, and the complete button is disabled

#### Scenario: Step 3 active - complete
- **WHEN** user views a pending order where all materials are confirmed and both product_shipping and logistics images are uploaded
- **THEN** the image upload section is collapsed, and the complete button is enabled with a pulse dot animation

### Requirement: Pulse dot animation replaces shake animation
The system SHALL use a pulsing dot animation instead of the left-right shake animation to draw user attention to the next actionable item.

#### Scenario: Pulse dot on unconfirmed material item
- **WHEN** a material item in a pending order is unconfirmed
- **THEN** a pulsing dot indicator appears next to the "待分配" button

#### Scenario: Pulse dot on empty image upload area
- **WHEN** an image upload area (product_shipping or logistics) has zero images in step 2
- **THEN** a pulsing dot indicator appears on the upload trigger area

#### Scenario: No pulse dot on completed item
- **WHEN** a material item is already confirmed or an image is already uploaded
- **THEN** no pulse dot indicator is shown

### Requirement: Collapsible material list
The system SHALL allow the material list card in sales order detail to be collapsed and expanded.

#### Scenario: Toggle material list collapse
- **WHEN** user taps the material list card header
- **THEN** the material list toggles between expanded and collapsed state with a rotating arrow indicator

#### Scenario: Auto-collapse when all materials confirmed
- **WHEN** all materials in a pending order are confirmed
- **THEN** the material list auto-collapses

### Requirement: Logistics image upload auto-confirms express
The system SHALL automatically set `express_confirmed` to `true` when a logistics-type image is uploaded to a sales order.

#### Scenario: Upload logistics image triggers express confirmation
- **WHEN** user uploads an image with `image_type=logistics` to a pending sales order
- **THEN** the order's `express_confirmed` field is automatically set to `true`

#### Scenario: Express confirmation without separate button
- **WHEN** user views a pending order where logistics image has been uploaded
- **THEN** the express status shows as confirmed without needing a separate confirm-express button

