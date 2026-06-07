## ADDED Requirements

### Requirement: Upload completion image for sales order
The system SHALL allow users to upload images to a sales order in `pending` status, with a required `image_type` field that MUST be either `product_shipping` or `logistics`.

#### Scenario: Upload product shipping image
- **WHEN** user uploads an image file with `image_type=product_shipping` to a sales order in `pending` status
- **THEN** the system stores the image and returns the image record with `id`, `image_url`, `image_type`, and `created_at`

#### Scenario: Upload logistics image
- **WHEN** user uploads an image file with `image_type=logistics` to a sales order in `pending` status
- **THEN** the system stores the image and returns the image record with `image_type=logistics`

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

### Requirement: View sales order images
The system SHALL return all images associated with a sales order, grouped by `image_type`.

#### Scenario: List images for an order
- **WHEN** user requests images for a sales order
- **THEN** the system returns a list of all images with `id`, `image_url`, `image_type`, `sort_order`, and `created_at`

#### Scenario: Empty image list for new order
- **WHEN** user requests images for a sales order that has no uploaded images
- **THEN** the system returns an empty list

### Requirement: Delete sales order image
The system SHALL allow users to delete an individual image from a sales order.

#### Scenario: Delete an uploaded image
- **WHEN** user deletes an image by its ID
- **THEN** the system removes the image file and database record, returning 204 No Content

#### Scenario: Delete non-existent image
- **WHEN** user attempts to delete an image ID that does not exist
- **THEN** the system returns a 404 error

### Requirement: Completion images required for order completion
The system SHALL require at least one `product_shipping` image and at least one `logistics` image to be uploaded before a sales order can be completed.

#### Scenario: Complete order with both images
- **WHEN** user completes a sales order that has both product_shipping and logistics images, all items confirmed, and express confirmed
- **THEN** the system transitions the order status to `completed`

#### Scenario: Reject completion missing product shipping image
- **WHEN** user attempts to complete a sales order that has a logistics image but no product_shipping image
- **THEN** the system returns a 400 error with message indicating the product shipping image is required

#### Scenario: Reject completion missing logistics image
- **WHEN** user attempts to complete a sales order that has a product shipping image but no logistics image
- **THEN** the system returns a 400 error with message indicating the logistics image is required

#### Scenario: Reject completion missing both images
- **WHEN** user attempts to complete a sales order that has neither product_shipping nor logistics images
- **THEN** the system returns a 400 error with message indicating both images are required
