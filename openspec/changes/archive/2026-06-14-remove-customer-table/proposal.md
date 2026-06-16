## Why

当前 Customer（客户）作为独立数据表存在，包含 name、code、contact、phone、email、address 等多个字段，并有完整的 CRUD API 端点。但在实际业务中，销售订单只需要一段描述收货信息的自由文本（如"张三 138xxxx 北京市朝阳区"），独立的客户表增加了不必要的复杂度——维护客户数据模型、API 端点、前端页面都是额外负担。SalesOrder 表中已经存在 `customer_name` 和 `customer_address` 两个冗余字段，说明客户数据本质上就是订单的附属信息，不值得作为独立实体管理。

## What Changes

- **BREAKING**: 移除 `Customer` 数据模型及对应的 `customers` 数据库表
- **BREAKING**: 移除客户管理全部 API 端点（`/customers` CRUD）
- 在 `SalesOrder` 中新增 `customer_info` 字段（Text 类型），替代原有的 `customer_id`、`customer_name`、`customer_address`
- 移除 `SalesOrder.customer_id` 外键及 `SalesOrder.customer` relationship
- 移除 `CustomerCreate`、`CustomerUpdate`、`CustomerResponse`、`CustomerListResponse` 等 Schema
- 前端销售订单创建/详情/列表页面：用自由文本输入框替代客户选择器
- 数据库迁移：删除 `customers` 表，为 `sales_orders` 添加 `customer_info` 列

## Capabilities

### New Capabilities
<!-- 本次变更为简化操作，不引入新的能力规格 -->
（无）

### Modified Capabilities
- `sales-order-guided-workflow`: 销售订单的客户信息从「关联客户表 + 冗余字段」变为单一的 `customer_info` 自由文本字段，创建/编辑/详情页面的客户信息输入和展示方式发生变化

## Impact

| 层面 | 影响 |
|------|------|
| 数据库 | 删除 `customers` 表；`sales_orders` 表新增 `customer_info` 列，移除 `customer_id`、`customer_name`、`customer_address` 列 |
| 后端 API | 移除 `/customers` 全部端点；`/sales-orders` 创建/更新接口的客户相关字段变更 |
| 前端 | 销售订单创建页：客户选择器 → 文本输入框；列表/详情页：展示 `customer_info` 替代 `customer_name` |
| 现有数据 | 迁移脚本需将 `customer_name` + `customer_address` 合并写入 `customer_info`（如有数据） |
