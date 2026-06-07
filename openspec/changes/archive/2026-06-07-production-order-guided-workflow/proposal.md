## Why

生产订单详情页缺少引导式操作流程和产出实物留证。当前仅有简单的发布/完成按钮和 van-tag 状态显示，与已改造完成的销售订单引导式工作流体验差距大。需对齐：统一布局、逐步引导、产出图片留证、真实产出数量确认。

## What Changes

- 新增 `ProductionOrderImage` 模型和图片上传/查看/删除 API（仅产品图一种类型）
- **BREAKING**: `complete_production_order` 增加校验——必须上传产品图且确认产出数量
- 生产订单详情页全量重写为四步引导式工作流
- 新增「确认产出数量」步骤：生产人员输入真实产出的数量（考虑报废）
- 物料列表改为可折叠，物料检查按钮用 pulse-dot 提示
- 物料列表与产品图分开为独立卡片

## Capabilities

### New Capabilities
- `production-order-completion-images`: 产品图上传、管理、校验
- `production-order-guided-workflow`: 四步引导式工作流（检查物料→确认产出→上传产品图→完成）

### Modified Capabilities
- `inventory-lock-on-publish`: 生产订单发布时已锁定库存，本次补齐完成校验

## Impact

- **数据库**: 新增 `production_order_images` 表
- **后端**: `app/models/transaction.py` 新增模型；`app/routers/production_order.py` 新增图片路由 + 产出数量确认 + 完成校验
- **前端**: `web/src/api/production.ts` 新增图片 API + 产出入库 API；`web/src/types/production.ts` 新增类型；`ProductionOrderDetail.vue` 全量重写
