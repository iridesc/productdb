## 1. 数据库模型

- [x] 1.1 新增 `ProductionOrderImage` 模型到 `app/models/transaction.py`（仅 `product_shipping` 类型）
- [x] 1.2 `ProductionOrder` 添加 `images` 关系
- [x] 1.3 导出到 `app/models/__init__.py`

## 2. 后端 API

- [x] 2.1 新增 `POST /production-orders/{id}/images` 上传端点
- [x] 2.2 新增 `GET /production-orders/{id}/images` 查看端点
- [x] 2.3 新增 `DELETE /production-orders/images/{id}` 删除端点
- [x] 2.4 新增 `PUT /production-orders/{id}/yield` 产出数量确认端点
- [x] 2.5 `complete_production_order` 增加图片和产出数量校验
- [x] 2.6 `get_production_order` 添加 images eager loading
- [x] 2.7 更新 `ProductionOrderResponse` schema

## 3. 前端类型与 API

- [x] 3.1 `web/src/types/production.ts` 新增 `ProductionOrderImage` + `images` 字段
- [x] 3.2 `web/src/api/production.ts` 新增图片 API + 产出确认 API

## 4. 前端 UI 重写

- [x] 4.1 四步工作流进度条 + pulse-dot 动画 + step computed
- [x] 4.2 物料需求卡片：可折叠 + 逐个检查按钮
- [x] 4.3 产出数量确认卡片：输入框 + 确认按钮
- [x] 4.4 产品图上传统卡片
- [x] 4.5 完成按钮动态文案和状态
