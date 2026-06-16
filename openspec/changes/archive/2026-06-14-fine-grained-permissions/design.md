## Context

当前权限字段 `can_manage_sales`、`can_manage_production` 同时控制「查看模块」和「创建订单」两项能力。需要将创建权限拆分为独立字段。

`hasPermission()` 函数已实现 `is_superuser` 通配逻辑，新增字段无需修改 store。

## Goals / Non-Goals

**Goals:**
- 新增 `can_create_sales`、`can_create_production` 两个布尔权限字段
- 前端创建按钮根据创建权限显示/隐藏
- 创建页面（/sales-orders/create、/production-orders/create）权限门控改为检查创建权限
- 管理员可为每个用户单独配置创建权限

**Non-Goals:**
- 不改变「编辑/更新」权限（仍由模块权限控制）
- 不改变后端 API 权限检查（后端目前无权限限制，仅生产订单有 role 检查）
- 不变更物料模块权限模型

## Decisions

1. **创建权限默认关闭** — 新字段默认 `false`，管理员需显式开启。这符合最小权限原则。
2. **创建页面门控跟随创建权限** — `SalesOrderCreate.vue` 和 `ProductionOrderCreate.vue` 的权限检查改为 `can_create_*`，逻辑上创建页面只需要创建权限。
3. **is_superuser 自动绕过** — 无需为超级管理员单独设置，`hasPermission()` 对任何权限返回 true。

## Risks / Trade-offs

- **风险**: 极低。新字段默认 false，不影响现有超级管理员账号（已 UPDATE 设置为 true）
- **注意**: 之后创建的非管理员用户需要手动勾选「可创建」开关才能创建订单
