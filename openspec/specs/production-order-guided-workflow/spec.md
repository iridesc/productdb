# Production Order Guided Workflow

## Purpose

TBD

## Requirements

### Requirement: Guided four-step workflow for production orders
The system SHALL present the in-production order detail page as a four-step guided workflow: check materials → confirm yield → upload product image → complete.

#### Scenario: Step 1 - material checking active
- **WHEN** user views an in-production order where not all materials are checked
- **THEN** the material list shows unchecked items with pulse dot animation, subsequent steps are locked

#### Scenario: Step 2 - yield confirmation active
- **WHEN** all materials are checked but yield not confirmed
- **THEN** yield confirmation stepper input appears with pulse dot, defaulting to planned quantity

#### Scenario: Step 3 - product image upload active
- **WHEN** yield is confirmed but product image not uploaded
- **THEN** product image upload card appears with pulse dot

#### Scenario: Step 4 - complete active
- **WHEN** all materials checked, yield confirmed, and product image uploaded
- **THEN** complete button is enabled with pulse dot

### Requirement: Yield confirmation with stepper UI
The system SHALL provide a +/- stepper for yield quantity confirmation, defaulting to the planned quantity, with minimum 1 and maximum of the planned quantity.

### Requirement: Separate cards for each step
The system SHALL display material checking, yield confirmation, and product image upload as separate card modules.

### Requirement: Pulse dot animation
The system SHALL use pulse dot animation on the next actionable step.

### Requirement: Collapsible material list
The system SHALL allow the material list to be collapsed and expanded.

### Requirement: Production list shows product thumbnail
The system SHALL display the produced product's thumbnail image in the production order list, not material images.
