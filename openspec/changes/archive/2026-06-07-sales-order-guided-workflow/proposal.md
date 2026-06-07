## Why

当前销售订单待处理页面的操作按钮分散、缺乏明确的步骤引导，用户不清楚应该先做什么后做什么。按钮左右晃动动画不够直观，需要改为更温和的点状脉冲动画来引导注意力。同时，独立的"确认物流单号"按钮步骤多余——上传物流凭证图片本身就意味着确认物流。

## What Changes

- 待处理状态改为**分步解锁**的引导式工作流：步骤1分配物料 → 步骤2上传图片 → 步骤3完成订单
- 将按钮的 `shake` 左右晃动动画替换为**脉冲圆点动画**（pulse dot），在待操作项旁边显示跳动的小圆点提示
- **BREAKING**: 移除独立的"确认物流单号"按钮——上传物流凭证图片时自动将 `express_confirmed` 设为 `true`，上传即确认。删除 `POST /sales-orders/{id}/confirm-express` 端点
- 物料列表面板改为**可折叠**（默认展开），节省页面空间
- 完成按钮仅在全部物料已分配 + 两张凭证图片均已上传后才变为可点击状态，引导文案按步骤变化
- 处于前面步骤未完成时，后续步骤区域显示为锁定/不可操作状态

## Capabilities

### New Capabilities
- `sales-order-guided-workflow`: 销售订单待处理状态的引导式分步工作流、脉冲动画提示、物料列表折叠、物流图片上传自动确认

### Modified Capabilities
- `sales-order-completion-images`: 物流凭证图片上传时自动完成物流确认，不再需要单独的确认物流端点

## Impact

- **后端**: `app/routers/sales_order.py` — 删除 `confirm_express` 端点；物流图片上传时自动设置 `express_confirmed = True`；`complete_sales_order` 校验条件调整
- **前端**: `web/src/views/sales/SalesOrderDetail.vue` — 重构 pending 状态 UI 为分步工作流；替换动画为 pulse dot；物料列表折叠；移除确认物流按钮
- **前端 API**: `web/src/api/sales.ts` — 删除 `confirmExpress` 函数
