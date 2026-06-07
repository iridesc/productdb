## ADDED Requirements

### Requirement: Publish sales order locks inventory
The system SHALL check all product inventory levels when publishing a sales order from draft to pending status, and SHALL deduct the required quantities from `current_stock` atomically. If any product has insufficient stock, the publish operation SHALL be rejected with a 400 error.

#### Scenario: Publish with sufficient stock
- **WHEN** user publishes a sales order in draft status and all products have `current_stock >= quantity`
- **THEN** the system deducts all product quantities from stock, records SALES_OUT transactions, sets all items to `is_confirmed = True`, and transitions the order to pending

#### Scenario: Publish with insufficient stock
- **WHEN** user publishes a sales order in draft status and any product has `current_stock < quantity`
- **THEN** the system returns a 400 error specifying which product has insufficient stock, and no stock is deducted

### Requirement: Confirm sales order item is a no-op for inventory
The system SHALL treat `confirm_sales_order_item` as a marking-only operation that does not modify inventory. Inventory is already deducted at publish time.

#### Scenario: Confirm item after publish
- **WHEN** user confirms a sales order item in pending status
- **THEN** the item is marked `is_confirmed = True` without any stock change

### Requirement: Distribute production item is marking-only
The system SHALL treat `distribute_production_item` as a consumption tracking operation that updates `consumed_quantity` but does not deduct from `current_stock`.

#### Scenario: Distribute material to production item
- **WHEN** user distributes material to a production order item in IN_PRODUCTION status
- **THEN** the item's `consumed_quantity` is incremented without changing `material.current_stock`

### Requirement: Cancel production order returns inventory
The system SHALL return all consumed quantities back to stock when cancelling a production order in IN_PRODUCTION status.

#### Scenario: Cancel in-production order
- **WHEN** user cancels a production order in IN_PRODUCTION status
- **THEN** all consumed quantities are added back to each material's `current_stock`, ADJUSTMENT transactions are recorded, and the order status is set to CANCELLED
