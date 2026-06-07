# Product Selector

## Purpose

ProductSelector 是一个可复用的产品选择弹窗组件，用于在订单创建等场景中选择物料/产品。

## Requirements

### Requirement: Product selector loads available materials
The ProductSelector component SHALL load and display all materials when opened, without filtering by `is_active` status.

#### Scenario: Product selector opens in sales order creation
- **WHEN** user clicks "添加产品" on the sales order creation page
- **THEN** the ProductSelector popup opens and displays the list of all available materials

#### Scenario: Product selector with search
- **WHEN** user types a keyword in the ProductSelector search bar
- **THEN** the product list SHALL filter to show only materials matching the keyword by name or code
