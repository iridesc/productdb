## Why

创建销售订单页面中，「添加产品」弹窗（ProductSelector 组件）打开后无法显示可选产品，列表始终为空。这导致用户无法为销售订单添加物料。

## What Changes

- **ProductSelector 组件**：移除 `is_active: true` 过滤条件，与 `SalesOrderDetail.vue` 中的内联产品选择器行为保持一致（不额外过滤）
- 确保弹窗打开时能正常加载并展示所有物料

## Capabilities

### New Capabilities
- `product-selector`: ProductSelector 组件在创建销售订单等场景中正确加载并展示可选产品列表

### Modified Capabilities
<!-- None — no existing specs need modification -->

## Impact

- `web/src/components/ProductSelector.vue`: 修改 `loadProducts` 函数中的查询参数，移除 `is_active: true`
