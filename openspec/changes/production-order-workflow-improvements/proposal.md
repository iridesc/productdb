## Why

生产订单模块存在多个前后端不一致的问题：产品名称无法显示、缺少物料检查入口导致无法完成报工、状态机有过多的中间状态。同时用户反馈列表信息不足、详情页缺少草稿编辑功能。需要一次系统性改进，对齐销售订单的引导式工作流模式。

## What Changes

- **列表页改进**：修复产品名称无法正确展示的 bug（字段路径错误）；新增产品缩略图列和备注列；数量显示为整数
- **草稿编辑**：详情页支持编辑草稿订单的产品、数量、备注，修改产品/数量时自动重新生成 BOM
- **简化状态机**：移除「生产中」状态，流程简化为 草稿 → 待生产 → 已完成；开工端点改为 no-op；工人只看到待生产订单
- **引导式工作流**：对齐销售订单 4 步模式——步骤①检查物料 → 步骤②确认产出数量 → 步骤③上传产品图 → 步骤④报工完成；前一步未完成则后续步骤不可操作
- **产出数量支持 0**：允许确认产出为 0（弹出二次确认），不能超过计划数量；使用 +/- 步进器编辑
- **相机拍照上传**：产品图上传改为调用相机拍照（对齐销售订单），不再从文件选取
- **进度条置顶**：工作流步骤进度条置于详情页最顶部

## Capabilities

### New Capabilities
<!-- 无新增 capability，所有变更均在已有 spec 范围内 -->

### Modified Capabilities
- `production-order-lifecycle`: 移除「生产中」状态，简化状态机为 draft → pending → completed；修改开工、完成、取消、分配物料、确认产出、上传图片端点的状态校验
- `production-order-guided-workflow`: 新增 4 步引导式工作流（物料检查→产出确认→图片上传→报工完成）；步骤进度条置顶；草稿编辑模式；产出数量为 0 的二次确认；相机拍照替代文件选取

## Impact

- **后端**: `app/routers/production_order.py`（状态校验逻辑变更、编辑端点重写）、`app/schemas/__init__.py`（`ProductionOrderUpdate` 新增字段、`YieldUpdate` 允许 0）、`app/models/transaction.py`（`completed_quantity` 默认 None）
- **前端**: `ProductionOrderDetail.vue`（重大重写：工作流、相机、编辑模式）、`ProductionOrderList.vue`（新增列、修复字段）、`web/src/api/production.ts`（新增 `updateProductionOrder`）、`web/src/types/production.ts`（新增 `ProductionOrderUpdate` 类型）
- **无破坏性变更**：旧「生产中」状态数据兼容显示，端点保留但不再使用
