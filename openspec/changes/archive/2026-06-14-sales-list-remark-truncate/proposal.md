## Why

销售订单列表页目前只展示了订单号、状态、客户、金额、商品数、创建时间。备注（remark）列完全缺失 — 运营人员无法在列表中快速看到订单备注。同时客户信息（customer_info）可能很长（地址+电话+姓名），列表直接展示会撑破列宽。

## What Changes

- 销售订单列表新增「备注」列，展示 `remark` 字段
- 备注和客户信息过长时用省略号截断（CSS `text-overflow: ellipsis`）
- 点击截断的文本弹出 `van-dialog` 展示完整内容
- 列宽调整以容纳新列

## Capabilities

### New Capabilities
（无新能力 — 纯 UI 改进）

### Modified Capabilities
- `sales-order-guided-workflow`: 列表页展示规范变更 — 新增备注列，长文本截断+弹窗

## Impact

| 层面 | 影响 |
|------|------|
| 后端 | 无 |
| 前端 | `SalesOrderList.vue`：表格新增备注列，备注和客户信息列添加截断+点击弹窗逻辑 |
