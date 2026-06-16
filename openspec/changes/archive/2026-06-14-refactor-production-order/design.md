# 设计文档：重构生产订单流程

## 一、状态机设计

### 1.1 状态定义

```
┌──────────┐   发布(publish)   ┌──────────┐   开工(start)    ┌─────────────┐   报工(complete)   ┌──────────┐
│   草稿    │───────────────▶  │  待生产   │───────────────▶  │   生产中      │────────────────▶  │  已完成   │
│  draft   │                  │ pending  │                  │ in_production│                  │completed │
└──────────┘                  └──────────┘                  └──────────────┘                  └──────────┘
     │                             │                              │
     │ 删除(delete)                │ 取消(cancel)                  │ 不可取消
     ▼                             ▼                              │
  订单删除                      ┌──────────┐                      │
                               │  已取消   │                      │
                               │ cancelled│                      │
                               └──────────┘                      │
                                                                  │
   状态流转规则:                                                   │
   ────────────                                                   │
   draft       → pending     (publish: 校验库存 + 扣减)            │
   draft       → deleted     (delete: 直接删除,无库存影响)          │
   pending     → in_production (start: 库存不变)                   │
   pending     → cancelled   (cancel: 退回已扣物料库存)            │
   in_production → completed (complete: 成品入库)                  │
   in_production → (不可取消)                                      │
   completed   → 终态                                              │
   cancelled   → 终态                                              │
```

### 1.2 各状态说明

| 状态 | 枚举值 | 可见性 | 可执行操作 | 库存影响 |
|------|--------|--------|-----------|---------|
| 草稿 | `draft` | 仅运营/管理员 | 编辑、删除、发布 | 无 |
| 待生产 | `pending` | 运营+工人+管理员 | 开工、取消 | 发布时已扣物料 |
| 生产中 | `in_production` | 运营+工人+管理员 | 报工 | 无变化 |
| 已完成 | `completed` | 所有人 | 无 | 报工时成品入库 |
| 已取消 | `cancelled` | 所有人 | 无 | 取消时退回物料(如已扣) |

### 1.3 当前代码状态枚举变更

```python
# 之前
class ProductionOrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# 之后
class ProductionOrderStatusEnum(str, enum.Enum):
    DRAFT = "draft"            # 新增
    PENDING = "pending"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

---

## 二、库存变化时序

```
  创建         发布(扣物料)        开工          报工(入成品)       取消(退物料)
   │               │               │                │                 │
   ▼               ▼               ▼                ▼                 ▼
┌──────┐       ┌──────┐        ┌──────┐        ┌──────┐          ┌──────┐
│ 库存  │       │ 物料  │        │ 库存  │        │ 成品  │          │ 物料  │
│ 不变  │       │  -N  │        │ 不变  │        │  +N  │          │  +N  │
└──────┘       └──────┘        └──────┘        └──────┘          └──────┘
                   │                                  │                │
                   ▼                                  ▼                ▼
              库存流水                            库存流水          库存流水
         (production_out)                    (production_in)    (adjustment)
```

---

## 三、API 端点设计

### 3.1 端点列表

| 方法 | 路径 | 角色 | 说明 |
|------|------|------|------|
| GET | `/production-orders` | 认证用户 | 列表（运营看全部，工人看 pending+in_production） |
| POST | `/production-orders` | operator, admin | 创建生产订单（draft 状态） |
| GET | `/production-orders/{id}` | 认证用户 | 订单详情 |
| PUT | `/production-orders/{id}` | operator, admin | 更新草稿订单 |
| DELETE | `/production-orders/{id}` | operator, admin | 删除草稿订单 |
| PUT | `/production-orders/{id}/publish` | operator, admin | 发布：校验库存 + 扣减 |
| PUT | `/production-orders/{id}/start` | worker, admin | 开工 |
| PUT | `/production-orders/{id}/complete` | worker, admin | 报工：成品入库 |
| PUT | `/production-orders/{id}/cancel` | operator, admin | 取消待生产订单 + 退库存 |
| GET | `/production-orders/{id}/materials` | 认证用户 | 物料需求列表 |

### 3.2 关键端点详细逻辑

#### 3.2.1 创建订单 (POST)

```
输入: product_id, quantity, start_date?, end_date?, sales_order_id?, remark?
行为:
  1. 校验 product 存在
  2. 校验 sales_order 存在(如有)
  3. 生成订单号
  4. 根据 BOM 自动展开物料需求,创建 ProductionOrderItem
  5. 状态 = draft
  6. 不扣库存
```

#### 3.2.2 发布订单 (PUT /{id}/publish)

```
前提: 订单状态 = draft
行为:
  1. 检查订单有至少一个 item
  2. 逐个检查每个 item 的物料库存是否充足
     - 不足: 返回 400,列出所有缺料项
  3. 全部充足: 逐个扣减物料库存 + 生成 production_out 流水
  4. 状态 = pending
```

#### 3.2.3 开工 (PUT /{id}/start)

```
前提: 订单状态 = pending
行为:
  1. 状态 = in_production
  2. 库存无变化
```

#### 3.2.4 报工完成 (PUT /{id}/complete)

```
前提: 订单状态 = in_production
行为:
  1. 状态 = completed
  2. 成品入库: product.current_stock += order.quantity
  3. 生成 production_in 流水
  4. completed_quantity = quantity
```

#### 3.2.5 取消订单 (PUT /{id}/cancel)

```
前提: 订单状态 = pending
行为:
  1. 退回已扣物料库存
  2. 生成 adjustment 流水(标注来自取消)
  3. 状态 = cancelled

注意: 生产中不可取消,草稿用 delete 而非 cancel
```

---

## 四、多角色权限设计

### 4.1 数据模型

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│   User   │       │   UserRole   │       │   Role   │
│          │       │              │       │          │
│  id      │──┐    │  user_id  ───┼──────▶│  code    │
│  username│  └───▶│  role_code ──┼──┐    │  name    │
│  ...     │       │  created_at  │  │    │  description│
└──────────┘       └──────────────┘  │    └──────────┘
                                     │
                                     └───────────────┘
                                      多对多关联表
```

### 4.2 角色定义

| 角色编码 | 名称 | 生产订单权限 |
|----------|------|-------------|
| `admin` | 管理员 | 所有操作 |
| `operator` | 运营 | 创建/编辑/删除草稿、发布、取消待生产、查看全部 |
| `worker` | 工人 | 查看待生产+生产中、开工、报工 |
| `sales` | 销售 | 暂无（后续销售订单模块使用） |
| `shipping` | 发货 | 暂无（后续销售订单模块使用） |

### 4.3 权限检查实现

使用 FastAPI dependency：

```python
def require_roles(*roles: str):
    """要求用户至少拥有指定角色之一"""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        user_roles = {ur.role_code for ur in current_user.roles}
        if "admin" in user_roles:
            return current_user  # admin 拥有一切权限
        if not user_roles.intersection(roles):
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return role_checker
```

### 4.4 列表过滤逻辑

```python
def get_production_orders(...):
    query = db.query(ProductionOrder)
    user_roles = {ur.role_code for ur in current_user.roles}

    # worker 只能看到 pending + in_production(除非也有 operator 角色)
    if "worker" in user_roles and "operator" not in user_roles and "admin" not in user_roles:
        query = query.filter(
            ProductionOrder.status.in_([
                ProductionOrderStatusEnum.PENDING,
                ProductionOrderStatusEnum.IN_PRODUCTION,
            ])
        )
    # operator/admin 看到全部
```

---

## 五、订单号生成重构

### 5.1 当前问题

```python
def generate_production_no(db: Session) -> str:
    total_order_count = db.query(ProductionOrder).count() + 1
    return f"P-{total_order_count:03d}"
```

`count() + 1` 在并发下不原子，两个请求可能读到同一个 count，生成重复订单号。

### 5.2 新方案：时间戳 + 随机数

```python
def generate_production_no(db: Session) -> str:
    """生成生产单号: P-YYMMDD-XXXX"""
    from datetime import datetime
    import random
    date_part = datetime.utcnow().strftime("%y%m%d")
    rand_part = f"{random.randint(0, 9999):04d}"
    return f"P-{date_part}-{rand_part}"
```

由于订单号字段有 `unique` 约束，如果极低概率碰撞，数据库会报 IntegrityError，调用方可重试。生产订单量级下此方案足够。

---

## 六、数据模型变更汇总

### 6.1 新增模型

```python
class Role(Base):
    __tablename__ = "roles"
    code = Column(String(20), primary_key=True)  # admin/operator/worker/sales/shipping
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)

class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    role_code = Column(String(20), ForeignKey("roles.code"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 6.2 修改模型

| 模型 | 字段 | 变更 |
|------|------|------|
| `ProductionOrderStatusEnum` | - | 增加 `DRAFT = "draft"` |
| `User` | `roles` relationship | 新增，指向 UserRole |

### 6.3 初始化数据

系统启动时自动创建 5 个角色（admin, operator, worker, sales, shipping）。现有用户默认分配 admin 角色。

---

## 七、前端设计

### 7.1 视图路由

```
/production-orders          → 生产订单列表（按角色过滤）
/production-orders/create   → 创建生产订单（仅运营可见）
/production-orders/:id      → 生产订单详情（含操作按钮）
```

### 7.2 详情页操作按钮

| 状态 | 运营看到的按钮 | 工人看到的按钮 |
|------|-------------|-------------|
| draft | 编辑、删除、发布 | （不可见此订单） |
| pending | 取消 | 开工 |
| in_production | （无操作） | 报工完成 |
| completed | （无操作） | （无操作） |
| cancelled | （无操作） | （无操作） |

### 7.3 列表过滤

- 运营/管理员：显示全部状态的订单，可按状态筛选
- 纯工人：仅显示待生产和生产中的订单
