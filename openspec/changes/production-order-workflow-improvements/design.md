## Context

当前生产订单模块存在状态机过于复杂（含 4 个活跃状态）、前后端不一致（字段路径错误）、详情页缺少操作入口（物料检查按钮缺失）等问题。销售订单已实现成熟的 4 步引导式工作流模式，本次改造对齐该模式。

## Goals / Non-Goals

**Goals:**
- 简化生产订单状态机：draft → pending → completed
- 对齐销售订单的 4 步引导式工作流 UI 模式
- 支持草稿二次编辑（产品、数量、备注）
- 产出数量支持 0（含二次确认）和步进器编辑
- 产品图上传改为相机拍照
- 列表页修复产品名称、新增图片列和备注列

**Non-Goals:**
- 不修改销售订单任何代码
- 不改变库存扣减逻辑（发布时一次性扣减不变）
- 不改变 BOM 自动生成逻辑（仅在参数变更时触发重建）

## Decisions

### 1. 状态机简化策略

**决定**：移除「生产中」(in_production) 状态，所有操作直接在「待生产」(pending) 状态进行。

**理由**：「生产中」状态仅起标记作用，无库存变化，增加了操作步骤。移除后工人无需点击「开工」按钮，直接进行物料检查、产出确认、上传图片、报工完成。

**兼容性**：保留 `IN_PRODUCTION` 枚举值和「生产中」状态映射，旧数据仍可正常显示和完成报工。开工端点改为 no-op。

### 2. 工作流 UI 模式

**决定**：复用销售订单的 4 步工作流 UI 组件（.workflow-steps / .wf-step / .pulse-dot 等），通过 computed 属性控制步骤解锁。

**步骤定义**：
- step1Done = 所有物料 consumed_quantity >= quantity
- step2Done = completed_quantity != null（已确认产出）
- step3Done = images.length > 0（已上传产品图）
- step4Ready = step1 && step2 && step3

**理由**：复用已有 CSS 和交互模式，保持 UI 一致性，减少新增代码量。

### 3. completed_quantity 默认值变更

**决定**：将 DB 默认值从 `0` 改为 `None`（nullable=True）。

**理由**：需要区分「未设置产出」（null）和「确认产出为 0」（0）。step2Done 判断使用 `!= null` 而非 `> 0`。前端 `Number()` 处理 null → 0 → 显示为 0。

**数据迁移**：现有 `completed_quantity = 0` 的行会被当作「未确认产出」处理（step2Done = false），需要手动确认产出后方向报工完成。这是可接受的行为——存量订单本身也未完成。

### 4. 相机拍照替代文件上传

**决定**：复用销售订单的相机取景器实现（navigator.mediaDevices.getUserMedia + canvas 截图 + File 构造）。

**理由**：生产现场需要现场拍照留证，从相册选取不符合实际使用场景。代码与销售订单完全一致，维护成本低。

### 5. 草稿编辑时的 BOM 重建策略

**决定**：修改产品或数量时，删除全部旧 ProductionOrderItem，基于新参数重新从 BOM 计算生成。

**理由**：BOM 物料与产品强绑定，无法逐个增量更新。删除重建保证数据一致性。

## Risks / Trade-offs

- **存量 in_production 订单**：仍可通过旧代码路径报工完成，不影响已有数据。但新创建订单不会再进入此状态。
- **completed_quantity 数据迁移**：存量 `completed_quantity = 0` 的 pending 订单需要重新确认产出方向完成，增加一步操作。影响量小（存量 pending 订单通常很少）。
- **相机权限兼容性**：非 HTTPS 环境下 getUserMedia 可能不可用，已添加 catch 提示用户检查权限。
