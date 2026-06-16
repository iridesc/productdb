## ADDED Requirements

### Requirement: Fine-grained create permissions for sales and production orders
The system SHALL separate "create" permissions from "view" permissions for sales and production modules. The `can_create_sales` and `can_create_production` boolean flags SHALL control whether a user can create new orders, independently of whether they can view existing orders.

#### Scenario: User with view but not create permission sees no create button
- **WHEN** a user with `can_manage_sales=true` and `can_create_sales=false` views the sales order list
- **THEN** the "+" create button is not visible

#### Scenario: User with create permission can access create page
- **WHEN** a user with `can_create_sales=true` navigates to `/sales-orders/create`
- **THEN** the create form is displayed

#### Scenario: User without create permission gets blocked on create page
- **WHEN** a user with `can_create_sales=false` navigates to `/sales-orders/create`
- **THEN** a "暂无权限" message is displayed instead of the form

#### Scenario: Superuser has automatic create permission
- **WHEN** a superuser (`is_superuser=true`) accesses any page
- **THEN** all create buttons are visible and all create pages are accessible regardless of `can_create_*` flag values

#### Scenario: Admin can configure create permissions per user
- **WHEN** a superuser edits a user in the account management page
- **THEN** switches for "可创建销售订单" and "可创建生产订单" are displayed and can be toggled

#### Scenario: Create permission defaults to false for new users
- **WHEN** a superuser creates a new user
- **THEN** the "可创建销售订单" and "可创建生产订单" switches default to off
