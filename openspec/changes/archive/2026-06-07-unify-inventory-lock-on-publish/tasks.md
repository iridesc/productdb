## 1. 销售订单：发布时锁定库存

- [x] 1.1 修改 `publish_sales_order`：增加库存检查 + 一次性扣减 + 标记所有 item 为 `is_confirmed`
- [x] 1.2 修改 `confirm_sales_order_item`：去掉库存扣减和交易记录，改为纯标记操作

## 2. 生产订单：修复双重扣减和取消不回退

- [x] 2.1 修改 `distribute_production_item`：去掉库存扣减和交易记录，改为仅更新 `consumed_quantity`
- [x] 2.2 修改 `cancel_production_order`：IN_PRODUCTION 状态下退回库存

## 3. 验证

- [x] 3.1 构建前端并部署，验证发布→分配→完成流程
