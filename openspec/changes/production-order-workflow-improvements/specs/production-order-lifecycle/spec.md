## REMOVED Requirements

### Requirement: in_production（生产中）状态
**Reason**: 状态机过度设计——「生产中」仅作标记作用，无库存变化，增加了工人的多余操作步骤（开工按钮）。简化后可减少状态数量，提升操作效率。
**Migration**: 保留 `IN_PRODUCTION` 枚举值兼容旧数据。旧 in_production 订单仍可正常显示和报工完成。新创建订单不再进入此状态。

## MODIFIED Requirements

### Requirement: pending（待生产）

- 运营人员发布订单后进入的状态。
- 发布时如果订单没有物料需求（如订单创建后 BOM 才设置），系统应当自动根据当前 BOM 重新生成；如果仍然没有 BOM，拒绝发布。
- 发布时系统必须校验所有 BOM 物料的当前库存是否充足。
- 库存不足时错误信息应当列出所有缺料项（物料名称、编码、当前库存、需要数量），前端应当展示带物料详情页超链接的详细信息。
- 发布时系统必须扣减所有 BOM 物料的库存，并生成对应的 `production_out` 库存流水。
- 工人可在待生产状态下看到订单并进行全部操作。

**允许的操作**：
- 物料检查（标记 BOM 物料为已消耗）
- 确认产出数量（包括 0，需二次确认）
- 上传产品图（相机拍照）
- 报工完成（进入 completed 状态，成品入库）
- 取消（退回已扣物料，进入 cancelled 状态）

### Requirement: 状态流转规则

```
draft → pending       (publish)
draft → deleted       (delete)
pending → completed   (complete)
pending → cancelled   (cancel)
```

**不允许的流转**：
- pending → draft（不可回退到草稿）
- completed → 任何状态（已完成是终态）
- cancelled → 任何状态（已取消是终态）

### Requirement: 库存变化规则

| 事件 | 库存变化 | 流水类型 |
|------|---------|----------|
| 创建订单 | 无变化 | 无 |
| 发布订单 | 物料 -N（按 BOM 需求） | `production_out` |
| 物料检查 | 无变化 | 无 |
| 确认产出 | 无变化 | 无 |
| 报工完成 | 成品 +N（按实际产出数量） | `production_in` |
| 取消订单 | 物料 +N（退回已扣） | `adjustment` |
| 删除草稿 | 无变化 | 无 |

## ADDED Requirements

### Requirement: 草稿编辑

处于草稿状态的订单 SHALL 允许运营人员编辑产品、生产数量和备注。

#### Scenario: 编辑产品触发 BOM 重建
- **WHEN** 运营人员修改草稿订单的产品
- **THEN** 系统删除旧的物料需求列表，基于新产品的 BOM 重新生成物料需求

#### Scenario: 编辑数量触发 BOM 重算
- **WHEN** 运营人员修改草稿订单的生产数量
- **THEN** 系统基于新数量重新计算所有 BOM 物料的需求量

#### Scenario: 仅编辑备注不触发 BOM 重建
- **WHEN** 运营人员仅修改草稿订单的备注
- **THEN** 系统只更新备注字段，不重新生成物料需求

### Requirement: 产出数量可以为 0

确认产出数量时 SHALL 允许设置为 0（表示本次无成功产出）。

#### Scenario: 产出为 0 需要二次确认
- **WHEN** 用户将产出数量设为 0 并点击确认
- **THEN** 系统弹出确认对话框，提示确认后显示"已确认产出为 0"

#### Scenario: 产出不能超过计划数量
- **WHEN** 用户输入超过计划数量的值
- **THEN** 系统拒绝并提示"产出数量不得超过计划数量"

#### Scenario: completed_quantity 区分未设置和设为 0
- **WHEN** 订单刚发布（completed_quantity 为 None）
- **THEN** 步骤②（确认产出）显示为未完成
- **WHEN** 用户确认产出为 0（completed_quantity 设为 0）
- **THEN** 步骤②显示为已完成
