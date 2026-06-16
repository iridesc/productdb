## Why

当前权限模型为粗粒度「模块可见性」控制：`can_manage_sales` 控制用户能否看到销售模块，`can_manage_production` 控制能否看到生产模块。但实际业务中，用户可能需要查看订单但不能创建订单。例如质检员需要查看销售订单确认物料，但不应有权创建新订单。

需要将「创建」权限从「查看」权限中分离出来，实现更细粒度的访问控制。

## What Changes

- 新增两个数据库字段：`can_create_sales`、`can_create_production`（默认 false）
- 登录 API 响应中包含新字段
- 用户创建/编辑表单中新增对应开关
- `hasPermission()` 函数通过 `is_superuser` 通配符自动兼容新权限
- 前端按钮根据新权限显示/隐藏：
  - 销售订单列表页「+」按钮 → `can_create_sales`
  - 销售订单创建页访问 → `can_create_sales`
  - 生产订单列表页「+」按钮 → `can_create_production`
  - 生产订单创建页访问 → `can_create_production`
  - 物料详情「创建生产订单」按钮 → `can_create_production`

## Capabilities

### New Capabilities
- `fine-grained-create-permissions`: 细粒度创建权限，将创建操作从模块可见权限中独立出来

### Modified Capabilities
<!-- 无现有 capability 变动 -->

## Impact

- **数据库**: `users` 表新增 2 列
- **后端**: `app/models/transaction.py`、`app/schemas/__init__.py`、`app/routers/auth.py`、`app/routers/users.py`
- **前端**: `web/src/types/user.ts`、`web/src/store/user.ts`、`BottomTabBar.vue`、`AccountManagement.vue`、`SalesOrderList.vue`、`SalesOrderCreate.vue`、`ProductionOrderList.vue`、`ProductionOrderCreate.vue`、`MaterialDetail.vue`
