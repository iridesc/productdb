## MODIFIED Requirements

### Requirement: Upload completion image for sales order
The system SHALL allow users to upload images to a sales order in `pending` status, with a required `image_type` field that MUST be either `product_shipping` or `logistics`. When `image_type=logistics`, the system SHALL automatically set the order's `express_confirmed` to `true`.

#### Scenario: Upload product shipping image
- **WHEN** user uploads an image file with `image_type=product_shipping` to a sales order in `pending` status
- **THEN** the system stores the image and returns the image record with `id`, `image_url`, `image_type`, and `created_at`

#### Scenario: Upload logistics image auto-confirms express
- **WHEN** user uploads an image file with `image_type=logistics` to a sales order in `pending` status
- **THEN** the system stores the image, returns the image record, and automatically sets `express_confirmed` to `true` on the order

#### Scenario: Reject upload for non-pending order
- **WHEN** user attempts to upload an image to a sales order not in `pending` status
- **THEN** the system returns a 400 error with message indicating only pending orders can upload images

#### Scenario: Reject invalid image type
- **WHEN** user uploads an image with `image_type` other than `product_shipping` or `logistics`
- **THEN** the system returns a 422 validation error

#### Scenario: Reject invalid file format
- **WHEN** user uploads a file that is not an allowed image format (jpg, jpeg, png, gif, webp)
- **THEN** the system returns a 400 error with message indicating supported formats

#### Scenario: Reject oversized file
- **WHEN** user uploads an image file larger than 5MB
- **THEN** the system returns a 400 error with message indicating the file size limit
