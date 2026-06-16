## Context

当前系统中客户（Customer）作为独立实体存储在 `customers` 表中，通过 `customer_id` 外键关联到销售订单。同时 SalesOrder 表已有 `customer_name` 和 `customer_address` 两个冗余字段。前端销售订单创建页通过独立输入框填写客户名称。

实际使用场景中，客户信息仅作为收货信息的自由文本备注，不需要结构化存储和独立管理。移除客户表可以简化数据模型、减少 API 端点、降低前端复杂度。

## Goals / Non-Goals

**Goals:**
- 移除 `Customer` 模型、`customers` 数据库表及全部客户 CRUD API
- 在 `SalesOrder` 中用单一的 `customer_info` Text 字段替代 `customer_id` + `customer_name` + `customer_address`
- 前端用多行文本输入框替代客户选择器/独立输入框
- 迁移现有数据：将 `customer_name` 和 `customer_address` 合并到 `customer_info`

**Non-Goals:**
- 不改变销售订单的状态机或工作流逻辑
- 不影响其他模型对 Customer 的引用（经检查，仅 SalesOrder 引用了 Customer）
- 不改变生产订单模块的任何行为

## Decisions

### 字段设计

`customer_info` 使用 SQLAlchemy `Text` 类型（PostgreSQL `TEXT`），可存任意长度的客户/收货信息。

Schema 定义：
```python
# SalesOrderBase 中
customer_info: Optional[str] = Field(None, max_length=500)
```

### 数据库迁移策略

由于 SQLite/PostgreSQL 均不支持直接修改列，采用以下策略：

1. 添加 `customer_info` 列（可空的 Text）
2. 执行数据迁移：`UPDATE sales_orders SET customer_info = TRIM(COALESCE(customer_name, '') || ' ' || COALESCE(customer_address, ''))`
3. 删除 `customer_name`、`customer_address`、`customer_id` 列
4. 删除 `customers` 表

**备选方案**：使用 Alembic 迁移脚本自动执行以上步骤（当前项目无 Alembic，改为在 `Base.metadata.create_all` 后手动执行 SQL）。

### 前端适配

- 销售订单创建页：将 `customer_name` 输入框替换为一个 `customer_info` 多行文本输入框（textarea）
- 列表页：`item.customer_name` → `item.customer_info`
- 详情页：展示 `customer_info` 文本

## Risks / Trade-offs

- [数据丢失风险] 删除 `customers` 表后，原有客户数据（code, contact, phone, email）永久丢失 → 迁移前自动备份：将 `customer_name`、`customer_address` 合并写入 `customer_info`，其他字段丢弃（用户已确认不需要）
- [前端兼容性] TypeScript 类型变更可能导致编译错误 → 逐个检查 `SalesOrder`、`SalesOrderCreate`、`SalesOrderUpdate` 类型定义
- [API 兼容性] 移除 `/customers` 端点后，如有外部系统调用将失败 → 经检查，前端 SalesOrderCreate 页面使用独立输入框而不调用客户 API，无外部依赖
