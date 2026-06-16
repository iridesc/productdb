## 1. 列表页改进

- [ ] 1.1 修复产品名称显示：`item.product_name` → `item.product?.name`
- [ ] 1.2 新增产品缩略图列（状态与产品名称之间），无图片显示占位符
- [ ] 1.3 新增备注列（物料种类与创建时间之间），超长省略号截断
- [ ] 1.4 数量显示用 Number() 转为整数

## 2. 草稿编辑功能

- [ ] 2.1 前端 API 新增 `updateProductionOrder` 函数
- [ ] 2.2 前端类型新增 `ProductionOrderUpdate` 接口
- [ ] 2.3 后端 `ProductionOrderUpdate` schema 新增 `product_id`、`quantity` 字段
- [ ] 2.4 后端 `update_production_order` 端点：修改产品/数量时自动删除旧 BOM 并重新生成
- [ ] 2.5 详情页新增编辑模式（`isEditing`）：产品选择器、数量、备注
- [ ] 2.6 草稿操作区新增「编辑草稿」按钮

## 3. 简化状态机（移除 in_production）

- [ ] 3.1 后端 `get_production_orders` 工人过滤改为仅显示 PENDING
- [ ] 3.2 后端 `start_production_order` 改为 no-op（不再转换状态）
- [ ] 3.3 后端 `complete_production_order` 状态校验 IN_PRODUCTION → PENDING
- [ ] 3.4 后端 `set_production_yield` 状态校验 IN_PRODUCTION → PENDING
- [ ] 3.5 后端 `distribute_production_item` 状态校验 IN_PRODUCTION → PENDING
- [ ] 3.6 后端 `upload_production_order_image` 状态校验 IN_PRODUCTION → PENDING
- [ ] 3.7 后端 `cancel_production_order` 移除 IN_PRODUCTION 拦截逻辑
- [ ] 3.8 前端详情页移除「开工」按钮，报工完成移至待生产状态

## 4. 引导式工作流（对齐销售订单）

- [ ] 4.1 添加步骤计算（step1Done/step2Done/step3Done/step4Ready）
- [ ] 4.2 添加工作流步骤进度条（4 步圆圈+连线）
- [ ] 4.3 进度条部署于详情页最顶部
- [ ] 4.4 物料卡片：每个物料显示缩略图 + 「待检查」按钮（脉冲动画） + 已检查状态
- [ ] 4.5 产出确认卡片：van-stepper（+/-）内联在「完成数量」行，min=0, max=计划数量
- [ ] 4.6 产品图卡片：已上传图片展示 + 拍照按钮
- [ ] 4.7 报工完成按钮根据 step4Ready 启用/禁用，未就绪时显示当前卡住的步骤
- [ ] 4.8 后端 `import distributeProductionItem` 到详情页

## 5. 产出数量支持 0

- [ ] 5.1 后端 `YieldUpdate` schema：`gt=0` → `ge=0`
- [ ] 5.2 后端 `completed_quantity` 默认值：`default=0` → `nullable=True, default=None`
- [ ] 5.3 后端 `ProductionOrderResponse.completed_quantity`：`Decimal` → `Optional[Decimal]`
- [ ] 5.4 后端 `complete_production_order` 检查：`<= 0` → `is None`
- [ ] 5.5 前端 `step2Done` 判断：`> 0` → `!= null`
- [ ] 5.6 前端 `handleSetYield`：产出 0 时弹出 `showConfirmDialog` 二次确认

## 6. 相机拍照上传

- [ ] 6.1 添加相机状态变量（showCamera, videoRef, canvasRef, cameraStream）
- [ ] 6.2 实现 openCamera / closeCamera / capturePhoto 函数
- [ ] 6.3 添加相机取景器 van-popup（视频 + canvas + 拍摄按钮）
- [ ] 6.4 替换 van-uploader 为 upload-trigger（拍照按钮）
- [ ] 6.5 添加相机和上传相关 CSS 样式
