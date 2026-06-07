## 1. 数据库模型

- [x] 1.1 在 `app/models/transaction.py` 中新增 `SalesOrderImage` 模型（含 `SalesOrderImageType` 枚举），建立与 `SalesOrder` 的关系
- [x] 1.2 在 `app/models/__init__.py` 中导出 `SalesOrderImage` 和 `SalesOrderImageType`

## 2. 后端 API

- [x] 2.1 在 `app/routers/sales_order.py` 中新增 `POST /sales-orders/{order_id}/images` 上传端点（校验 pending 状态、image_type、文件格式/大小）
- [x] 2.2 在 `app/routers/sales_order.py` 中新增 `GET /sales-orders/{order_id}/images` 查看端点
- [x] 2.3 在 `app/routers/sales_order.py` 中新增 `DELETE /sales-orders/images/{image_id}` 删除端点
- [x] 2.4 修改 `complete_sales_order` 函数：增加 product_shipping 和 logistics 图片各至少一张的校验

## 3. 前端类型与 API

- [x] 3.1 在 `web/src/types/sales.ts` 中新增 `SalesOrderImage` 接口和 `SalesOrderImageType` 类型
- [x] 3.2 在 `web/src/api/sales.ts` 中新增 `uploadSalesOrderImage`、`getSalesOrderImages`、`deleteSalesOrderImage` 三个 API 函数

## 4. 前端 UI

- [x] 4.1 在 `web/src/views/sales/SalesOrderDetail.vue` 中新增图片上传区域（两个卡片：产品发货图 + 物流凭证图），含上传/预览/删除交互
- [x] 4.2 修改完成按钮逻辑：两张图片均上传后才可点击"完成订单"
