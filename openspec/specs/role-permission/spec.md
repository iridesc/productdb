# 角色权限系统

## Purpose

定义系统的多角色权限管理，包括 5 个内置角色的权限矩阵、权限检查实现方式以及前端行为规范。

## Requirements

### Requirement: 五角色定义

系统应当支持以下 5 个内置角色：

| 角色编码 | 角色名称 | 说明 |
|----------|----------|------|
| `admin` | 管理员 | 拥有系统所有权限 |
| `operator` | 运营 | 负责物料管理、库存调整、生产订单的创建和发布 |
| `worker` | 工人 | 负责领取生产订单、开工、报工 |
| `sales` | 销售 | 负责销售订单相关操作 |
| `shipping` | 发货 | 负责发货相关操作 |

#### Scenario: 角色与权限的关系

- **WHEN** 用户拥有 admin 角色
- **THEN** 该用户应当自动通过所有权限检查

- **WHEN** 用户拥有多个角色
- **THEN** 该用户的权限应当取所有角色权限的并集

### Requirement: 用户与角色的多对多关联

系统应当支持一个用户拥有多个角色，通过 `user_roles` 关联表实现。

#### Scenario: 数据模型

- **WHEN** 系统创建角色关联
- **THEN** 应当在 `user_roles` 表中建立 user_id 与 role_code 的关联记录
- **AND** 角色定义应当存储在 `roles` 表中（code 为主键）

### Requirement: 系统启动初始化

系统启动时应当自动初始化角色数据并保持向后兼容。

#### Scenario: 首次初始化

- **WHEN** 系统首次启动且 roles 表不存在任何角色
- **THEN** 应当自动创建 5 个默认角色（admin, operator, worker, sales, shipping）
- **AND** 应当为所有现有用户自动分配 admin 角色

#### Scenario: 幂等性

- **WHEN** 系统重启时 roles 表已存在角色
- **THEN** 不应当重复创建角色
- **AND** 不应当重复分配 admin 角色

### Requirement: 生产订单权限矩阵

生产订单的各操作应当根据角色进行权限控制。

| 操作 | operator | worker | admin |
|------|----------|--------|-------|
| 查看生产订单列表 | ✅ 全部 | ⚠️ 仅 pending + in_production | ✅ 全部 |
| 查看生产订单详情 | ✅ | ✅ | ✅ |
| 创建生产订单 | ✅ | ❌ | ✅ |
| 编辑草稿订单 | ✅ | ❌ | ✅ |
| 删除草稿订单 | ✅ | ❌ | ✅ |
| 发布订单 | ✅ | ❌ | ✅ |
| 开工 | ❌ | ✅ | ✅ |
| 报工完成 | ❌ | ✅ | ✅ |
| 取消待生产订单 | ✅ | ❌ | ✅ |

#### Scenario: 运营人员操作权限

- **WHEN** 用户拥有 operator 角色
- **THEN** 该用户应当可以创建、编辑、删除草稿、发布、取消生产订单
- **AND** 该用户不应当可以开工或报工

#### Scenario: 工人操作权限

- **WHEN** 用户拥有 worker 角色
- **THEN** 该用户应当可以开工和报工完成生产订单
- **AND** 该用户不应当可以创建、编辑、删除、发布或取消订单
- **AND** 该用户在生产订单列表应当仅看到 pending 和 in_production 状态的订单

#### Scenario: 管理员操作权限

- **WHEN** 用户拥有 admin 角色
- **THEN** 该用户应当可以执行生产订单的所有操作
- **AND** 该用户在生产订单列表应当看到所有状态的订单

### Requirement: 权限检查实现

权限检查应当使用 FastAPI Dependency 方式实现。

#### Scenario: require_roles dependency

- **WHEN** 端点标记 `require_roles("operator", "admin")`
- **THEN** 仅拥有 operator 或 admin 角色的用户可以通过
- **AND** 权限不足时应当返回 403 "权限不足"

- **WHEN** 用户拥有 admin 角色
- **THEN** 应当自动通过所有 `require_roles` 调用

### Requirement: 前端角色感知

前端应当根据当前用户角色显示或隐藏操作按钮和页面入口。

#### Scenario: 运营视角

- **WHEN** 运营角色用户访问生产订单列表
- **THEN** 应当显示创建订单的 "+" 按钮
- **AND** 应当显示所有状态的订单

#### Scenario: 工人视角

- **WHEN** 纯工人角色用户访问生产订单列表
- **THEN** 不应当显示创建订单的 "+" 按钮
- **AND** 应当仅显示 pending 和 in_production 状态的订单

#### Scenario: 页面刷新后角色恢复

- **WHEN** 用户在已登录状态下刷新页面
- **THEN** 系统应当从 localStorage 恢复 token
- **AND** 应当自动重新获取用户角色信息
