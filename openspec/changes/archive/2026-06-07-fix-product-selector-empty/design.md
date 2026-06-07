## Context

`ProductSelector.vue` 是一个可复用的产品选择弹窗组件，被 `SalesOrderCreate.vue` 页面用于在创建销售订单时选择物料。该组件在弹出时调用 `getMaterials()` API 加载物料列表。

当前 `ProductSelector` 在查询参数中硬编码了 `is_active: true`，而 `SalesOrderDetail.vue` 中的内联产品选择器（`loadProducts`）没有此过滤条件。两处行为不一致，且 `is_active: true` 可能导致物料列表返回空结果。

后端 `GET /materials` 接口支持 `is_active` 可选查询参数（`Optional[bool]`），默认为 `None`（不过滤）。`Material` 模型的 `is_active` 字段默认值为 `True`。

## Goals / Non-Goals

**Goals:**
- 修复 ProductSelector 弹窗打开后无法显示产品的问题
- 与 SalesOrderDetail 的产品选择器行为保持一致

**Non-Goals:**
- 不修改后端 API
- 不修改 SalesOrderDetail 或其他使用 getMaterials 的地方

## Decisions

**方案：移除 `is_active: true` 参数**

将 `ProductSelector.vue` 中 `loadProducts` 的查询参数从 `{ page_size: 100, is_active: true }` 改为 `{ page_size: 100 }`。

理由：
1. 后端 `is_active` 默认值为 `True`，新创建的物料默认就是活跃状态，无需前端额外过滤
2. 与 `SalesOrderDetail.vue` 中的 `loadProducts` 行为一致
3. 最小改动，风险最低

备选方案（已否决）：
- 添加错误提示/log：治标不治本，用户仍然无法选择产品
- 修改后端移除 `is_active` 支持：影响面大，其他调用方可能依赖此参数

## Risks / Trade-offs

- 如果将来确实需要在前端过滤非活跃物料，需要重新设计过滤逻辑。当前业务场景下，`is_active` 过滤不重要，因为物料默认就是活跃状态
