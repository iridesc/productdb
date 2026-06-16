## MODIFIED Requirements

### Requirement: Guided four-step workflow for production orders
The system SHALL present the pending (待生产) order detail page as a four-step guided workflow: check materials → confirm yield → upload product image → complete. The workflow progress bar SHALL be positioned at the top of the detail content.

#### Scenario: Step 1 - material checking active
- **WHEN** user views a pending order where not all materials are checked
- **THEN** each material item shows a "待检查" button with pulse dot animation; subsequent steps are locked

#### Scenario: Step 1 - material checked
- **WHEN** user clicks "待检查" button on a material item
- **THEN** system marks the material as consumed (consumed_quantity = quantity); button changes to "已检查" tag; when all materials checked, step 2 unlocks

#### Scenario: Step 2 - yield confirmation active
- **WHEN** all materials are checked but yield not confirmed
- **THEN** a van-stepper (+/- buttons) appears inline in the "完成数量" row for yield quantity input, with min 0 and max of planned quantity

#### Scenario: Step 2 - yield confirmed as zero
- **WHEN** user sets yield to 0 and clicks confirm
- **THEN** system shows a confirmation dialog; if confirmed, yield is set to 0 and step 3 unlocks

#### Scenario: Step 3 - product image upload active
- **WHEN** yield is confirmed but product image not uploaded
- **THEN** a "拍照" trigger button appears for camera-based image capture

#### Scenario: Step 3 - camera capture
- **WHEN** user clicks "拍照" button
- **THEN** system opens a full-screen camera viewfinder using rear camera; user can capture a photo which is compressed to JPEG and uploaded

#### Scenario: Step 4 - complete active
- **WHEN** all materials checked, yield confirmed, and product image uploaded
- **THEN** complete button is enabled with pulse dot; clicking it completes the order (成品入库)

### Requirement: Yield confirmation with stepper UI
The system SHALL provide a van-stepper (+/- buttons) for yield quantity confirmation, placed inline in the "完成数量" row, with minimum 0 and maximum of the planned quantity.

#### Scenario: Stepper adjusts yield quantity
- **WHEN** user taps + or - on the stepper
- **THEN** the yield quantity increments or decrements by 1, bounded by 0 and planned quantity

### Requirement: Production list shows product info correctly
The system SHALL display the product name from `product.name` (not `product_name`), product thumbnail image from `product.thumbnail_url`, and order remark in the production order list table.

#### Scenario: List displays product name
- **WHEN** production orders are loaded
- **THEN** each row shows the product name from the nested product object

#### Scenario: List displays product thumbnail
- **WHEN** a product has thumbnail_url
- **THEN** a 36px thumbnail image appears between the status and product name columns

#### Scenario: List displays remark
- **WHEN** an order has a remark
- **THEN** the remark appears in the remark column between material type count and created date

## ADDED Requirements

### Requirement: Draft order editing
The system SHALL allow editing of draft production orders directly from the detail page.

#### Scenario: Enter edit mode
- **WHEN** user views a draft order and clicks "编辑草稿"
- **THEN** the info card switches to a form with product selector, quantity input, and remark textarea

#### Scenario: Save edits
- **WHEN** user modifies fields and clicks "保存"
- **THEN** system updates the order; if product or quantity changed, BOM items are regenerated; page refreshes with updated data

### Requirement: Camera-based product image upload
The system SHALL use the device camera for product image capture instead of file picker, matching the sales order pattern.

#### Scenario: Open camera from placeholder
- **WHEN** user clicks the "拍照" upload trigger in the product image card
- **THEN** system opens a full-screen camera viewfinder with rear camera, cancel button, and capture button

#### Scenario: Capture and upload
- **WHEN** user taps the capture button
- **THEN** system captures a JPEG photo from the video stream, compresses to quality 0.9, validates size under 5MB, then uploads the image

#### Scenario: Camera permission denied
- **WHEN** camera access is denied by the browser
- **THEN** system shows a message "无法打开相机，请检查权限设置"

### Requirement: Quantity displayed as integer
All production order quantities SHALL be displayed as integers (using `Number()` conversion) to avoid showing decimal places like "1.00".

#### Scenario: Integer display
- **WHEN** a quantity value is 1 (stored as Decimal/Numeric)
- **THEN** it is displayed as "1", not "1.00"
