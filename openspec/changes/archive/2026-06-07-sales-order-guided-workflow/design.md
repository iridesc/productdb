## Context

当前 `SalesOrderDetail.vue` 的 pending 状态各种操作按钮（分配物料、确认物流、上传图片、完成订单）虽然已有条件显示，但缺少明确的步骤引导感。按钮使用左右晃动动画（`shake`）提示用户操作，视觉效果不够友好。独立存在的"确认物流单号"按钮增加了一次多余点击——上传物流凭证图片本身就应该视为物流确认。

## Goals / Non-Goals

**Goals:**
- 待处理状态 UI 改为三步引导式工作流：步骤①分配物料 → 步骤②上传凭证图片 → 步骤③完成订单
- 按钮动画从 shake 改为 pulse dot（脉动圆点），仅在"当前可操作但尚未完成"的步骤显示
- 物流凭证图片上传时自动触发 `express_confirmed = True`，无需单独确认步骤
- 物料列表默认折叠，节省垂直空间
- 未解锁步骤视觉上置灰/锁定，不可交互

**Non-Goals:**
- 不改变订单状态流转逻辑（draft → pending → completed/cancelled）
- 不改变产品发货图片的行为
- 不改变编辑模式（draft 状态）

## Decisions

### 1. 三步工作流状态机（纯前端 computed）

**选择:** 使用 `computed` 属性推导当前工作流步骤，不引入额外状态变量。

```
步骤判断逻辑:
- step1_done = 所有物料 is_confirmed
- step2_done = product_shipping 图片 >= 1 且 logistics 图片 >= 1
- step3_ready = step1_done && step2_done

UI 表现:
- step1 未完成: 物料列表展开，未分配项显示 pulse dot，图片上传区锁定(灰色)
- step1 完成 → step2 未完成: 物料列表折叠（显示"已全部分配"），图片上传区解锁 + pulse dot
- step2 完成: 图片上传区折叠，完成按钮可用 + pulse dot
```

### 2. 脉冲圆点动画（CSS）

**选择:** 使用纯 CSS `@keyframes` 实现 pulsing dot，替代 shake 动画。

```css
@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.5; }
}
```

在 `van-button` 旁添加一个 `<span class="pulse-dot"></span>`，仅在需要提示时显示。

### 3. 物流图片上传自动确认物流

**选择:** 在 `upload_sales_order_image` 的后端逻辑中，当 `image_type=logistics` 时自动将订单的 `express_confirmed` 设为 `True`。

前端移除了 `confirmExpress` 调用。物流图片上传成功后，`detail.express_confirmed` 会在 `fetchDetail/fetchOrderImages` 刷新后自动变为 `true`。

**替代方案:** 前端在上传成功后额外调一次 `confirmExpress` — 拒绝，增加不必要的网络请求。

### 4. 物料列表折叠（Vant Collapse 或手动实现）

**选择:** 使用手动的 `v-show` + 点击标题切换 `productsCollapsed` 状态。在 pending 状态下默认展开，待物料全部分配完毕后自动折叠。已完成的订单默认折叠。

简单的 `van-icon` 箭头旋转指示折叠状态，避免引入 `van-collapse` 组件的额外复杂性。

### 5. 移除 confirm_express 端点

**选择:** 删除 `PUT /sales-orders/{order_id}/confirm-express` 路由。这是一个 **BREAKING** 变更，但由于前端同步移除调用，影响范围可控。

## Risks / Trade-offs

- **向后兼容**: 删除 `confirm_express` API 端点，如果有外部系统调用会受影响 → 本项目为单体应用，无外部调用方
- **物流图片删除后 express_confirmed 状态**: 如果用户删除了物流图片，`express_confirmed` 不会自动回退 → 手动删除图片的场景极少，接受此行为。如需回退可手动调用 API
- **步骤判断依赖数据刷新**: `fetchDetail` 需要在每次操作后调用以刷新步骤状态 → 现有代码已满足此要求
