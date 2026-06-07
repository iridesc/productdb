## Context

当前销售订单和生产订单对库存扣减的时机不同，行为不一致：
- 销售订单：发布时不检查库存，逐项分配时扣减，取消时退回
- 生产订单：发布时一次性扣减，另有 distribute 再次扣减（双重扣减 bug），取消时不退回

统一为「发布即锁定」模式，发布 = 库存交给订单，后续分配只是确认/标记。

## Goals / Non-Goals

**Goals:**
- 销售订单发布时检查所有物料库存，不足则拒绝发布
- 销售订单发布时一次性扣减所有物料库存
- `confirm_sales_order_item` 改为纯标记，不再操作库存
- `distribute_production_item` 改为纯标记，不再重复扣减库存
- `cancel_production_order` 在 IN_PRODUCTION 状态下退回已扣库存

**Non-Goals:**
- 不改变前端 UI
- 不引入新的库存字段（如 reserved_stock）
- 不改变订单状态机

## Decisions

### 1. 方案 A：直接扣减 current_stock（采用）

发布时直接从 `material.current_stock` 扣除订单所需数量。取消时加回。

```
publish:  current_stock -= order.quantity  (all items at once)
cancel:   current_stock += order.quantity  (only confirmed items)
```

**替代方案 B（未采用）**: 新增 `reserved_stock` 字段。更精确但对现有系统改动大，当前不做。

### 2. 销售订单 publish 改为原子操作

`publish_sales_order` 新增逻辑：
```python
# 1. 检查所有物料库存
for item in order.items:
    if product.current_stock < item.quantity:
        raise 库存不足，拒绝发布

# 2. 一次性扣减
for item in order.items:
    product.current_stock -= item.quantity
    record InventoryTransaction(SALES_OUT)
    item.is_confirmed = True  # 发布即分配

# 3. 状态变更
order.status = PENDING
```

### 3. confirm_sales_order_item 降级为纯标记

去掉库存操作逻辑，只保留 `is_confirmed = True`。因为发布时已经设为 True，实际上这个端点变为幂等/辅助操作。

### 4. 生产订单修复

- `distribute_production_item`: 去掉 `material.current_stock -=` 和 `InventoryTransaction` 创建，只更新 `consumed_quantity`
- `cancel_production_order`: IN_PRODUCTION 状态下，遍历 items，将 consumed_quantity 加回 current_stock，记录 ADJUSTMENT 交易

## Risks / Trade-offs

- **销售订单发布即扣库存**：库存占用时间变长（从分配到完成）→ 可接受，这是标准 ERP 行为
- **并发**: 两个订单同时发布可能竞争同一库存 → 依赖数据库事务隔离，当前 PostgreSQL 默认 READ COMMITTED 已够用
- **confirm_sales_order_item 变为空操作**: 前端调用该端点仍返回成功，不影响现有 UI
