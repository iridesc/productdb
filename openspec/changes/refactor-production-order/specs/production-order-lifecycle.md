# 生产订单生命周期

## 概述

生产订单（Production Order）是运营人员根据产品库存情况创建的生产任务。订单经历草稿（draft）、待生产（pending）、生产中（in_production）、已完成（completed）四个活跃状态，以及已取消（cancelled）终态。

## 状态定义

### draft（草稿）

- 运营人员创建生产订单后的初始状态。
- 订单应当自动根据产品的 BOM 展开物料需求，生成 ProductionOrderItem 列表。
- 处于草稿状态的订单，工人不可见。
- 草稿状态下库存不发生任何变化。
- 运营人员应当在草稿阶段确认物料库存是否充足，不足时应当去采购并补充库存。

**允许的操作**：
- 编辑订单（修改数量、日期、备注等）
- 删除订单（从数据库中完全移除，无库存影响）
- 发布订单（进入 pending 状态）

### pending（待生产）

- 运营人员发布订单后进入的状态。
- 发布时系统必须校验所有 BOM 物料的当前库存是否充足。
- 发布时系统必须扣减所有 BOM 物料的库存，并生成对应的 `production_out` 库存流水。
- 工人可在待生产状态下看到订单并领取。

**允许的操作**：
- 开工（进入 in_production 状态）
- 取消（退回已扣物料，进入 cancelled 状态）

### in_production（生产中）

- 工人开工后进入的状态。
- 开工时库存无变化（物料已在发布时扣减）。
- 处于生产中的订单不可取消。

**允许的操作**：
- 报工完成（进入 completed 状态，成品入库）

### completed（已完成）

- 工人报工完成后进入的终态。
- 报工时系统必须将成品入库：`product.current_stock += order.quantity`。
- 报工时系统必须生成 `production_in` 库存流水。
- 成品入库成本按 BOM 理论成本计算（各物料 price × 用量 之和）。

### cancelled（已取消）

- 待生产状态的订单被运营取消后进入的终态。
- 取消时系统必须退回所有已扣减的物料库存。
- 取消时系统必须生成 `adjustment` 库存流水，标注来源为订单取消。
- 已取消的订单不可恢复。

## 状态流转规则

```
draft → pending       (publish)
draft → deleted       (delete)
pending → in_production (start)
pending → cancelled   (cancel)
in_production → completed (complete)
```

**不允许的流转**：
- in_production → cancelled（生产中不可取消）
- completed → 任何状态（已完成是终态）
- cancelled → 任何状态（已取消是终态）
- pending → draft（不可回退到草稿）

## 库存变化规则

| 事件 | 库存变化 | 流水类型 |
|------|---------|----------|
| 创建订单 | 无变化 | 无 |
| 发布订单 | 物料 -N（按 BOM 需求） | `production_out` |
| 开工 | 无变化 | 无 |
| 报工完成 | 成品 +N（按生产数量） | `production_in` |
| 取消订单 | 物料 +N（退回已扣） | `adjustment` |
| 删除草稿 | 无变化 | 无 |

## BOM 物料需求计算

发布订单时，物料需求数量 = 生产数量 × BOM用量 × (1 + 损耗率/100)。

例如：生产 100 把椅子，BOM 中椅腿用量为 4，损耗率为 5%，则椅腿需求 = 100 × 4 × 1.05 = 420。

## 订单号格式

新格式：`P-{YYMMDD}-{4位随机数}`

示例：`P-260602-3847`

替代旧格式（`P-{count:03d}`），避免并发碰撞。
