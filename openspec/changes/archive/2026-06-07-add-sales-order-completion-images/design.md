## Context

当前系统在销售订单流程的最后一步——完成订单时——仅检查两个条件：所有物料均已分配（`is_confirmed`）且物流单号已确认（`express_confirmed`）。缺少发货实况的图片留证，无法在事后追溯产品的实际发货状态或物流凭证。

系统已有物料图片上传机制（`MaterialImage` 模型 + `app/routers/image.py`），本次设计完全复用其模式：文件存储路径、格式校验、大小限制等保持一致。

## Goals / Non-Goals

**Goals:**
- 销售订单在 `pending` 状态下，用户可以上传两种图片：产品发货图、物流凭证图
- 每种图片至少需要上传 1 张，才能执行订单完成操作
- 已完成订单可以查看已上传的凭证图片
- 订单取消时允许清理已上传的图片
- 复用现有图片上传基础设施（存储路径、文件格式/大小校验）

**Non-Goals:**
- 不改变现有的物料图片上传功能
- 不改变订单的其他状态流转逻辑（草稿→待处理→已完成/已取消）
- 不支持图片编辑/裁剪（保持与物料图片一致）
- 不添加图片批量上传（同上，保持简单）

## Decisions

### 1. 数据模型：新建 `SalesOrderImage` 表

**选择:** 新建独立的 `sales_order_images` 表，含 `image_type` 字段区分图片类型。

```python
class SalesOrderImage(Base):
    __tablename__ = "sales_order_images"
    id: UUID (PK)
    order_id: UUID (FK → sales_orders.id, CASCADE)
    image_type: Enum('product_shipping', 'logistics')  # 图片类型
    image_url: String(500)
    sort_order: Integer (default 0)
    created_at: DateTime
```

**替代方案:**
- 复用 `MaterialImage` 表 — 拒绝，因为该表与物料强绑定（`material_id` FK），语义不匹配
- 直接加字段到 `SalesOrder` 表（如 `product_image_url`、`logistics_image_url`）— 拒绝，因为将来可能支持多张图片，VARCHAR 字段扩展性差

### 2. API 设计：在 sales_order router 中新增图片子路由

**选择:** 在 `app/routers/sales_order.py` 中直接增加图片上传/查看/删除端点，复用 `app/routers/image.py` 中的文件处理逻辑（路径 `UPLOAD_DIR`、扩展名白名单、5MB 限制）。

端点设计：
- `POST /sales-orders/{order_id}/images` — 上传图片（form-data: file + image_type）
- `GET /sales-orders/{order_id}/images` — 获取订单所有图片
- `DELETE /sales-orders/images/{image_id}` — 删除单张图片

**替代方案:**
- 独立 router 文件 — 拒绝，图片与订单紧密耦合，放在一起减少路由碎片化

### 3. 完成校验：在 `complete_sales_order` 中增加图片检查

**选择:** 在现有 `complete_sales_order` 函数中增加检查逻辑：
- 必须存在至少 1 张 `product_shipping` 类型的图片
- 必须存在至少 1 张 `logistics` 类型的图片
- 不满足时返回 400 错误，明确提示缺少哪种图片

### 4. 前端交互：图片上传区嵌入订单详情页

**选择:** 在 `SalesOrderDetail.vue` 的 `pending` 状态区域，在"完成订单"按钮上方增加两个上传卡片：
- 产品发货图片卡片（点击上传/预览/删除）
- 物流凭证图片卡片（点击上传/预览/删除）
- 两张图片均上传后，"完成订单"按钮才变为可点击状态

前端复用 `MaterialDetail.vue` 中的图片上传 UI 模式：`<input type="file" hidden>` + 点击触发。

## Risks / Trade-offs

- **数据库迁移**: 新增表需要执行 migration。当前项目无 Alembic 配置，采用 SQLAlchemy `create_all` 自动建表方式，部署重启后自动生效。
- **图片存储容量**: 每个订单至少 2 张图片，长期运营需要关注磁盘空间。→ 短期可接受；未来可考虑对象存储（OSS/MinIO）。
- **取消订单时的图片清理**: 取消订单时需要决定是否保留图片。→ 本次采用保留策略：图片仅通过 DELETE API 手动删除，取消订单不清除图片，避免误删证据。
