# Production Order Completion Images

## Purpose

TBD

## Requirements

### Requirement: Upload product image for production order
The system SHALL allow users to upload a product shipping image to a production order in `in_production` status.

#### Scenario: Upload product image
- **WHEN** user uploads an image file with `image_type=product_shipping` to a production order in `in_production` status
- **THEN** the system stores the image and returns the image record

#### Scenario: Reject upload for non-in-production order
- **WHEN** user attempts to upload an image to a production order not in `in_production` status
- **THEN** the system returns a 400 error

### Requirement: View and delete production order images
The system SHALL allow listing and deleting production order images.

#### Scenario: List images
- **WHEN** user requests images for a production order
- **THEN** the system returns all images for that order

#### Scenario: Delete image
- **WHEN** user deletes an image by its ID
- **THEN** the system removes the image and returns 204

### Requirement: Product image required for completion
The system SHALL require at least one product image to be uploaded before a production order can be completed.

#### Scenario: Complete with product image
- **WHEN** user completes an order with product image, yield confirmed, and all materials checked
- **THEN** the system transitions to `completed`

#### Scenario: Reject completion without product image
- **WHEN** user attempts to complete without product image
- **THEN** the system returns a 400 error

### Requirement: Confirm production yield
The system SHALL allow users to set the actual completed quantity on a production order.

#### Scenario: Set yield quantity
- **WHEN** user sets `completed_quantity` to the actual produced count on an in-production order
- **THEN** the system stores the value and validates it is >0 and ≤ planned quantity

#### Scenario: Yield required for completion
- **WHEN** user attempts to complete without confirming yield
- **THEN** the system returns a 400 error

### Requirement: Complete production increases product inventory
The system SHALL add the `completed_quantity` to the product's `current_stock` when completing a production order.

#### Scenario: Product stock increases on completion
- **WHEN** a production order is completed with `completed_quantity = N`
- **THEN** the product's `current_stock` increases by N and a PRODUCTION_IN transaction is recorded
