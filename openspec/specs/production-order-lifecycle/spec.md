# 生产订单生命周期

## Purpose

定义生产订单（Production Order）的完整生命周期管理，包括 5 状态流转、BOM 物料需求自动计算、库存变更规则以及订单号格式。

## Requirements

### Requirement: 五状态生命周期

生产订单应当支持以下 5 个状态：草稿（draft）、待生产（pending）、生产中（in_production）、已完成（completed）、已取消（cancelled）。

#### Scenario: 状态流转规则

- **WHEN** 订单处于 draft 状态且运营执行发布操作
- **THEN** 订单应当转换为 pending 状态

- **WHEN** 订单处于 draft 状态且运营执行删除操作
- **THEN** 订单应当被永久删除

- **WHEN** 订单处于 pending 状态且工人执行开工操作
- **THEN** 订单应当转换为 in_production 状态

- **WHEN** 订单处于 pending 状态且运营执行取消操作
- **THEN** 订单应当转换为 cancelled 状态

- **WHEN** 订单处于 in_production 状态且工人执行报工完成操作
- **THEN** 订单应当转换为 completed 状态

#### Scenario: 禁止的流转

- **WHEN** 尝试将 in_production 状态的订单取消
- **THEN** 系统应当拒绝并返回错误

- **WHEN** 尝试将 completed 或 cancelled 状态的订单变更到其他状态
- **THEN** 系统应当拒绝并返回错误

- **WHEN** 尝试将 pending 状态回退到 draft
- **THEN** 系统应当拒绝并返回错误

### Requirement: 草稿状态

生产订单创建时应当处于 draft（草稿）状态。草稿状态下库存不发生任何变化，工人不可见草稿订单。

#### Scenario: 创建草稿

- **WHEN** 运营人员创建生产订单
- **THEN** 订单应当以 draft 状态创建
- **AND** 系统应当自动根据产品 BOM 展开物料需求，生成 ProductionOrderItem 列表
- **AND** 库存不发生任何变化

#### Scenario: 草稿可编辑

- **WHEN** 订单处于 draft 状态
- **THEN** 运营人员可以编辑订单的字段（数量、日期、备注等）

#### Scenario: 草稿可删除

- **WHEN** 订单处于 draft 状态
- **THEN** 运营人员可以删除订单（从数据库完全移除，无库存影响）

### Requirement: 发布订单（draft → pending）

发布订单时，系统必须校验所有 BOM 物料的当前库存是否充足，库存充足时扣减物料库存并生成库存流水。

#### Scenario: 发布前自动生成物料需求

- **WHEN** 订单没有物料需求（如订单创建后 BOM 才设置）
- **THEN** 系统应当在发布时自动根据当前 BOM 重新生成物料需求
- **AND** 如果仍然没有 BOM，拒绝发布并提示"订单没有物料需求，无法发布"

#### Scenario: 库存充足时发布

- **WHEN** 所有 BOM 物料库存 ≥ 需求数量
- **THEN** 系统应当逐一扣减物料库存
- **AND** 为每个扣减生成 `production_out` 库存流水
- **AND** 订单状态转换为 pending

#### Scenario: 库存不足时拒绝发布

- **WHEN** 任一 BOM 物料库存 < 需求数量
- **THEN** 系统应当返回 400 错误
- **AND** 错误信息应当列出所有缺料项：物料名称、物料编码、当前库存、需要数量

### Requirement: 开工（pending → in_production）

工人应当可以开工待生产状态的生产订单，开工时库存无变化。

#### Scenario: 正常开工

- **WHEN** 工人对 pending 状态的订单执行开工操作
- **THEN** 订单状态转换为 in_production
- **AND** 库存不发生任何变化

#### Scenario: 非待生产状态不可开工

- **WHEN** 尝试对非 pending 状态的订单执行开工操作
- **THEN** 系统应当拒绝并返回错误

### Requirement: 报工完成（in_production → completed）

工人报工完成时，系统必须将成品入库并生成库存流水。

#### Scenario: 成品入库

- **WHEN** 工人对 in_production 状态的订单执行报工完成操作
- **THEN** 产品库存应当增加订单生产数量：`product.current_stock += order.quantity`
- **AND** 应当生成 `production_in` 库存流水
- **AND** `completed_quantity` 应当设置为 `quantity`
- **AND** 订单状态转换为 completed

#### Scenario: 非生产中状态不可报工

- **WHEN** 尝试对非 in_production 状态的订单执行报工完成操作
- **THEN** 系统应当拒绝并返回错误

### Requirement: 取消订单（pending → cancelled）

运营人员应当可以取消待生产状态的订单，取消时退回已扣减的物料库存。

#### Scenario: 退回物料库存

- **WHEN** 运营人员对 pending 状态的订单执行取消操作
- **THEN** 系统应当逐一退回所有已扣减的物料库存
- **AND** 为每个退回生成 `adjustment` 库存流水
- **AND** 订单状态转换为 cancelled

#### Scenario: 生产中不可取消

- **WHEN** 尝试取消 in_production 状态的订单
- **THEN** 系统应当拒绝并返回错误

### Requirement: 库存变化规则

系统应当按以下规则管理库存：

| 事件 | 库存变化 | 流水类型 |
|------|---------|----------|
| 创建订单 | 无变化 | 无 |
| 发布订单 | 物料 -N（按 BOM 需求） | `production_out` |
| 开工 | 无变化 | 无 |
| 报工完成 | 成品 +N（按生产数量） | `production_in` |
| 取消订单 | 物料 +N（退回已扣） | `adjustment` |
| 删除草稿 | 无变化 | 无 |

### Requirement: BOM 物料需求计算

物料需求数量应当 = 生产数量 × BOM 用量 × (1 + 损耗率 / 100)。

#### Scenario: 含损耗率的需求计算

- **WHEN** 生产数量为 100，BOM 用量为 4，损耗率为 5%
- **THEN** 计算物料需求 = 100 × 4 × 1.05 = 420

### Requirement: 订单号格式

订单号应当使用格式 `P-{YYMMDD}-{4位随机数}`，确保并发安全。

#### Scenario: 订单号生成

- **WHEN** 创建新生产订单
- **THEN** 订单号应当匹配 `P-YYMMDD-XXXX` 格式
- **AND** 使用 4 位随机数避免并发碰撞
