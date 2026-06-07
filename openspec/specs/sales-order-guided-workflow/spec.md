# Sales Order Guided Workflow

## Purpose

TBD

## Requirements

### Requirement: Guided step-by-step workflow for pending orders
The system SHALL present the pending sales order detail page as a four-step guided workflow where each step unlocks only after the previous step is completed.

#### Scenario: Step 1 active - material allocation
- **WHEN** user views a pending order where not all materials are confirmed
- **THEN** the material list is expanded by default with unconfirmed items showing a pulse dot animation, and image upload sections are hidden

#### Scenario: Step 2 active - product shipping image upload
- **WHEN** user views a pending order where all materials are confirmed but product shipping image is not uploaded
- **THEN** the material list collapses showing "已全部分配", the product shipping image upload area appears below the material list with pulse dot animation, and the logistics information card shows only the express number without upload area

#### Scenario: Step 3 active - logistics image upload
- **WHEN** user views a pending order where product shipping image is uploaded but logistics image is not
- **THEN** the logistics image upload area appears in the logistics information card with pulse dot animation

#### Scenario: Step 4 active - complete
- **WHEN** user views a pending order where all materials are confirmed and both product_shipping and logistics images are uploaded
- **THEN** the complete button is enabled with a pulse dot animation

### Requirement: Pulse dot animation replaces shake animation
The system SHALL use a pulsing dot animation instead of the left-right shake animation to draw user attention to the next actionable item.

#### Scenario: Pulse dot on unconfirmed material item
- **WHEN** a material item in a pending order is unconfirmed
- **THEN** a pulsing dot indicator appears next to the "待分配" button

#### Scenario: Pulse dot on empty product shipping image area
- **WHEN** step 1 is complete and product shipping image has not been uploaded
- **THEN** a pulsing dot indicator appears on the product shipping image upload area

#### Scenario: Pulse dot on empty logistics image area
- **WHEN** step 2 is complete and logistics image has not been uploaded
- **THEN** a pulsing dot indicator appears on the logistics image upload area

#### Scenario: No pulse dot on completed item
- **WHEN** a material item is already confirmed or an image is already uploaded
- **THEN** no pulse dot indicator is shown

### Requirement: Combined material and product shipping image module
The system SHALL combine the material list and product shipping image upload into a single card module on the sales order detail page.

#### Scenario: Product shipping image appears below material list
- **WHEN** all materials are confirmed in a pending order
- **THEN** the product shipping image upload area appears below the material items within the same card

#### Scenario: Product shipping image hidden when materials not confirmed
- **WHEN** not all materials are confirmed in a pending order
- **THEN** the product shipping image upload area is not visible

### Requirement: Separate logistics information module
The system SHALL display the express number and logistics image in a dedicated logistics information card, separate from the order information card.

#### Scenario: Logistics card shows express number
- **WHEN** user views a pending order
- **THEN** the logistics information card displays the express number

#### Scenario: Logistics image upload appears after product image uploaded
- **WHEN** the product shipping image has been uploaded
- **THEN** the logistics image upload area appears in the logistics information card

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
