## MODIFIED Requirements

### Requirement: Sales order list shows remark and truncates long text

The sales order list SHALL display a remark column and SHALL truncate long text in the customer info and remark columns, with tap-to-view-full-text behavior.

#### Scenario: Remark column displayed

- **WHEN** user views the sales order list
- **THEN** a "备注" column is displayed showing the `remark` value
- **AND** empty remarks display "-"

#### Scenario: Long remark truncated with ellipsis

- **WHEN** a sales order has a remark longer than the column width
- **THEN** the remark text is truncated with an ellipsis ("...")

#### Scenario: Tap truncated remark to view full text

- **WHEN** user taps a truncated remark text
- **THEN** a dialog popup displays the full remark text

#### Scenario: Long customer_info truncated with ellipsis

- **WHEN** a sales order has customer_info longer than the column width
- **THEN** the customer_info text is truncated with an ellipsis ("...")

#### Scenario: Tap truncated customer_info to view full text

- **WHEN** user taps a truncated customer_info text
- **THEN** a dialog popup displays the full customer_info text
