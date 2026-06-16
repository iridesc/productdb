# Sales Order Guided Workflow

## Purpose

TBD

## Requirements

### Requirement: Guided step-by-step workflow for pending orders
The system SHALL present the pending sales order detail page as a four-step guided workflow where each step unlocks only after the previous step is completed.

#### Scenario: Step 1 active - material confirmation
- **WHEN** user views a pending order where not all materials are confirmed
- **THEN** the material list is expanded by default with unconfirmed items showing a pulse dot animation, and image upload sections are hidden

#### Scenario: Step 2 active - material image upload
- **WHEN** user views a pending order where all materials are confirmed but material image is not uploaded
- **THEN** the material list collapses showing "已全部检查", the material image upload area appears below the material list with pulse dot animation, and the logistics information card shows only the express number without upload area

#### Scenario: Step 3 active - logistics image upload
- **WHEN** user views a pending order where material image is uploaded but logistics image is not
- **THEN** the logistics image upload area appears in the logistics information card with pulse dot animation

#### Scenario: Step 4 active - complete
- **WHEN** user views a pending order where all materials are confirmed and both material and logistics images are uploaded
- **THEN** the complete button is enabled with a pulse dot animation

### Requirement: Pulse dot animation replaces shake animation
The system SHALL use a pulsing dot animation instead of the left-right shake animation to draw user attention to the next actionable item.

#### Scenario: Pulse dot on unconfirmed material item
- **WHEN** a material item in a pending order is unconfirmed
- **THEN** a pulsing dot indicator appears next to the "待检查" button

#### Scenario: Pulse dot on empty material image area
- **WHEN** step 1 is complete and material image has not been uploaded
- **THEN** a pulsing dot indicator appears on the material image upload area

#### Scenario: Pulse dot on empty logistics image area
- **WHEN** step 2 is complete and logistics image has not been uploaded
- **THEN** a pulsing dot indicator appears on the logistics image upload area

#### Scenario: No pulse dot on completed item
- **WHEN** a material item is already confirmed or an image is already uploaded
- **THEN** no pulse dot indicator is shown

### Requirement: Combined material list and material image module
The system SHALL combine the material list and material image upload into a single card module on the sales order detail page.

#### Scenario: Material image appears below material list
- **WHEN** all materials are confirmed in a pending order
- **THEN** the material image upload area appears below the material items within the same card

#### Scenario: Material image hidden when materials not confirmed
- **WHEN** not all materials are confirmed in a pending order
- **THEN** the material image upload area is not visible

### Requirement: Separate logistics information module
The system SHALL display the express number and logistics image in a dedicated logistics information card, separate from the order information card.

#### Scenario: Logistics card shows express number
- **WHEN** user views a pending order
- **THEN** the logistics information card displays the express number

#### Scenario: Logistics image upload appears after material image uploaded
- **WHEN** the material image has been uploaded
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

### Requirement: Sales order uses customer_info free-text field

The system SHALL use a single `customer_info` free-text field for customer information on sales orders, replacing the previous `customer_id` (foreign key to customers table), `customer_name`, and `customer_address` fields.

The system SHALL NOT manage customers as independent entities — there shall be no customers table or customer CRUD API.

#### Scenario: Fill customer info when creating sales order

- **WHEN** user creates a sales order and fills in customer info
- **THEN** the system saves `customer_info` as a free-text string on the sales order
- **AND** the `customer_info` field can contain customer name, phone, address, and any other shipping information

#### Scenario: Display customer info on sales order detail

- **WHEN** user views a sales order detail
- **THEN** the order info section displays the full content of `customer_info`

#### Scenario: Edit customer info when updating sales order

- **WHEN** user edits a sales order
- **THEN** the `customer_info` field can be modified

#### Scenario: Display customer info in sales order list

- **WHEN** user views the sales order list
- **THEN** each order row displays the `customer_info` value, or "-" when empty

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

### Requirement: Unified material terminology in UI labels

The system SHALL use "物料" (material) as the unified Chinese label for all inventory items throughout the UI, including the sales order detail page. The term "产品" (product) SHALL NOT appear in user-facing labels on this page.

#### Scenario: Material list card header
- **WHEN** user views a sales order detail
- **THEN** the card containing the line items is labeled "物料列表"

#### Scenario: Workflow step 1 label
- **WHEN** user views a pending sales order
- **THEN** step 1 shows "检查物料" when incomplete and "物料已检查" when complete

#### Scenario: Workflow step 2 label
- **WHEN** user views a pending sales order
- **THEN** step 2 shows "物料图片" when incomplete and "物料图已上传" when complete

#### Scenario: Image upload section label
- **WHEN** the material image upload area is visible
- **THEN** its label reads "物料图片" (not "产品图片" or "产品发货图片")

#### Scenario: Empty state and action buttons
- **WHEN** the material list is empty or in edit mode
- **THEN** the empty text reads "暂无物料" and the add button reads "添加物料"

#### Scenario: Material picker labels
- **WHEN** the material picker popup is open
- **THEN** the search placeholder reads "搜索物料名称或编码" and empty state reads "无匹配物料"
