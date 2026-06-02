# 任务清单

## 阶段 1：数据模型变更

### T1.1 修改 ProductionOrderStatusEnum

- [x] 在 `app/models/transaction.py` 中给 `ProductionOrderStatusEnum` 增加 `DRAFT = "draft"` 枚举值
- [x] 确认枚举值顺序为：DRAFT → PENDING → IN_PRODUCTION → COMPLETED → CANCELLED

### T1.2 新增 Role 和 UserRole 模型

- [x] 在 `app/models/transaction.py` 中新增 `Role` 模型（表名 `roles`）
- [x] 在 `app/models/transaction.py` 中新增 `UserRole` 模型（表名 `user_roles`）
- [x] 给 `User` 模型添加 `roles` relationship（指向 UserRole）
- [x] 更新 `app/models/__init__.py` 导出新模型

### T1.3 数据库初始化

- [x] 在 `app/main.py` 的 `lifespan` 中添加角色自动创建逻辑（5 个角色的 upsert）
- [x] 添加现有用户自动分配 admin 角色的迁移逻辑（仅在 roles 表为空时执行）
- [x] 验证数据库自动建表 `Base.metadata.create_all` 会创建新表

---

## 阶段 2：后端 — 角色权限基础设施

### T2.1 角色权限 dependency

- [x] 在 `app/utils/auth.py` 中新增 `require_roles(*roles)` 函数
- [x] 实现逻辑：admin 角色自动通过；否则检查用户角色是否与所需角色有交集
- [x] 权限不足时返回 403 `"权限不足"`

### T2.2 角色管理 API（可选）

- [x] 在 `app/routers/auth.py` 中新增 `GET /auth/me/roles` 端点，返回当前用户的角色列表
- [x] 供前端判断当前用户权限

---

## 阶段 3：后端 — 生产订单重构

### T3.1 订单号生成重构

- [x] 修改 `generate_production_no` 函数为新格式：`P-{YYMMDD}-{4位随机数}`
- [x] 文件：`app/routers/production_order.py`

### T3.2 创建订单逻辑修改

- [x] 修改 `create_production_order`：订单创建时状态设为 `DRAFT`
- [x] 创建时不扣库存（当前代码已不扣，确认即可）
- [x] 创建订单需要 `require_roles("operator", "admin")`

### T3.3 新增发布端点 `PUT /{id}/publish`

- [x] 新增 `publish_production_order` 端点
- [x] 校验状态 == DRAFT
- [x] 校验订单有至少一个 item
- [x] 逐个检查 BOM 物料库存是否充足
- [x] 库存不足时返回 400，列出所有缺料项（物料名称 + 当前库存 + 需要数量）
- [x] 库存充足时逐个扣减物料库存
- [x] 为每个扣减生成 `production_out` 库存流水
- [x] 状态 → PENDING
- [x] 需要 `require_roles("operator", "admin")`

### T3.4 新增开工端点 `PUT /{id}/start`

- [x] 新增 `start_production_order` 端点
- [x] 校验状态 == PENDING
- [x] 状态 → IN_PRODUCTION
- [x] 库存无变化
- [x] 需要 `require_roles("worker", "admin")`

### T3.5 重写完成端点

- [x] 改造现有的 `update_production_status` 中的完成逻辑为独立端点 `PUT /{id}/complete`
- [x] 校验状态 == IN_PRODUCTION
- [x] 成品入库：`product.current_stock += order.quantity`
- [x] 生成 `production_in` 库存流水
- [x] `completed_quantity = quantity`
- [x] 状态 → COMPLETED
- [x] 需要 `require_roles("worker", "admin")`

### T3.6 新增取消端点 `PUT /{id}/cancel`

- [x] 新增 `cancel_production_order` 端点
- [x] 校验状态 == PENDING（生产中不可取消）
- [x] 退回所有已扣物料库存（遍历 items）
- [x] 为每个退回生成 `adjustment` 库存流水
- [x] 状态 → CANCELLED
- [x] 需要 `require_roles("operator", "admin")`

### T3.7 修改删除端点

- [x] 修改 `delete_production_order`：仅 DRAFT 可删除
- [x] 需要 `require_roles("operator", "admin")`

### T3.8 修改列表端点

- [x] 修改 `get_production_orders`：根据用户角色过滤
- [x] 纯工人角色仅显示 PENDING + IN_PRODUCTION
- [x] 运营/管理员显示全部

### T3.9 废弃旧的状态变更端点（可选）

- [x] 移除 `PUT /{id}/status` 端点（由专用端点替代）

---

## 阶段 4：前端适配

### T4.1 API 层更新

- [x] 在 `web/src/api/production.ts` 中添加新端点调用（publish, start, complete, cancel）
- [x] 添加 `getCurrentUserRoles` API 调用

### T4.2 角色状态管理

- [x] 在 `web/src/store/user.ts` 中存储用户角色列表
- [x] 登录后自动获取用户角色

### T4.3 生产订单列表页改造

- [x] 纯工人视角：仅显示待生产和生产中订单，隐藏创建按钮
- [x] 运营视角：显示全部状态，可筛选

### T4.4 创建订单页（原 ProductionOrderCreate.vue）

- [x] 创建后订单处于草稿状态
- [x] 展示 BOM 物料需求预览
- [x] 草稿状态可编辑/删除

### T4.5 订单详情页改造（原 ProductionOrderDetail.vue）

- [x] 按状态和角色显示不同操作按钮（参考 design.md §7.2）
- [x] 草稿：编辑/删除/发布（仅运营）
- [x] 待生产：取消（运营）/开工（工人）
- [x] 生产中：报工完成（工人）
- [x] 已完成/已取消：无操作

### T4.6 前端路由守卫

- [x] 在 `router/index.ts` 中实现 `requiresAuth` 检查
- [x] 未登录重定向到 `/login`

---

## 阶段 5：验证与测试

### T5.1 手动测试

- [ ] 运营创建草稿 → 发布（库存充足/不足两种场景）→ 工人开工 → 工人报工 → 验证成品入库
- [ ] 运营创建草稿 → 发布 → 工人开工 → 运营尝试取消（应被拒绝）
- [ ] 运营创建草稿 → 发布 → 取消 → 验证物料库存退回
- [ ] 工人尝试创建订单（应被拒绝）
- [ ] 工人尝试发布订单（应被拒绝）
- [ ] 用户有 operator + worker 角色时验证所有操作正常
- [ ] 订单号格式验证（新格式 P-YYMMDD-XXXX）

### T5.2 运行已有测试

- [x] 确保 `test_order_no_v2.py` 通过（该测试针对销售订单，不受本次变更影响）
- [x] 检查是否有其他测试需要更新（无其他现有测试）

---

## 依赖关系

```
T1.1 ──┬── T3.2 ── T3.3 ── T3.4 ── T3.5 ── T3.6
       │
T1.2 ──┼── T2.1 ── T2.2
       │         │
T1.3 ──┘         └── 所有 T3 任务依赖 T2.1

T3.x 全部完成 → T4.x
T4.x 全部完成 → T5.x
```
