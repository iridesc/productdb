## Why

销售订单完成时需要上传两张凭证图片（产品发货照片 + 物流凭证照片），作为订单完成的必要前置条件。当前系统在分配物料和确认物流后即可直接点击"完成订单"，缺少图片留证环节，无法追溯发货实况。

## What Changes

- 新增 `SalesOrderImage` 数据库模型，存储销售订单的完成凭证图片，区分 `product_shipping`（产品发货）和 `logistics`（物流凭证）两种类型
- 新增销售订单图片上传 API：上传、查看、删除图片
- **BREAKING**: `complete_sales_order` 增加校验——必须上传产品发货图 + 物流凭证图各至少一张，否则拒绝完成
- 前端销售订单详情页在待处理状态下展示图片上传区域，上传两张图片后方可点击"完成订单"按钮
- 已完成订单详情页展示已上传的凭证图片，支持点击预览

## Capabilities

### New Capabilities
- `sales-order-completion-images`: 销售订单完成凭证图片的上传、管理、查看功能，作为订单完成的前置强制条件

### Modified Capabilities
<!-- None - this is a new capability, not modifying existing spec requirements -->

## Impact

- **数据库**: 新增 `sales_order_images` 表
- **后端 API**: `app/routers/sales_order.py` 新增图片 CRUD 路由；`complete_sales_order` 增加图片检查逻辑
- **前端**: `web/src/api/sales.ts` 新增图片 API 函数；`web/src/types/sales.ts` 新增图片类型；`SalesOrderDetail.vue` 新增上传 UI 和完成按钮条件逻辑
- **依赖**: 复用现有的图片上传机制（`app/routers/image.py` 的上传/存储/删除模式）
