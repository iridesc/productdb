## Why

销售订单和生产订单的库存扣减时机不一致：销售订单在逐项分配时扣减，可能因库存不足卡在半途；生产订单发布时即扣减，但存在双重扣减和取消不回退的 bug。统一为「发布即锁定库存」模式，保证订单一旦发布即可完成。

## What Changes

- **BREAKING**: `publish_sales_order` 增加库存检查 + 一次性扣减，库存不足拒绝发布
- **BREAKING**: `confirm_sales_order_item` 改为纯标记操作，不再扣减库存（库存已在发布时扣完）
- 修复 `distribute_production_item`：改为纯标记（消耗量记录），不再重复扣减库存
- 修复 `cancel_production_order`：IN_PRODUCTION 状态下取消时退回已扣减的库存
- `cancel_sales_order` 保持现有退回逻辑不变

## Capabilities

### New Capabilities
- `inventory-lock-on-publish`: 统一的「发布即锁定库存」机制，销售订单发布时扣减库存、生产订单取消时退回库存

### Modified Capabilities
- `sales-order-guided-workflow`: 步骤①的「分配物料」操作改为纯标记确认，库存变更移至发布时
- `sales-order-completion-images`: 无直接变更，但完成校验中的库存状态不再相关

## Impact

- **后端**: `app/routers/sales_order.py` — `publish_sales_order` 加库存检查+扣减，`confirm_sales_order_item` 去掉扣减
- **后端**: `app/routers/production_order.py` — `distribute_production_item` 去掉扣减，`cancel_production_order` 加退回库存
- **前端**: 无变更（按钮文案和交互不变，只是后端行为变了）
