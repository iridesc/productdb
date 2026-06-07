## 1. 后端：物流图片上传自动确认

- [x] 1.1 修改 `upload_sales_order_image`：当 `image_type=logistics` 时自动设置 `express_confirmed = True`
- [x] 1.2 删除 `PUT /sales-orders/{order_id}/confirm-express` 端点
- [x] 1.3 调整 `complete_sales_order` 校验逻辑：移除单独的 `express_confirmed` 检查（物流图片上传已自动确认）

## 2. 前端 API 清理

- [x] 2.1 删除 `web/src/api/sales.ts` 中的 `confirmExpress` 函数

## 3. 前端 UI：脉冲动画与工作流

- [x] 3.1 用 pulse-dot CSS 动画替换所有 `action-btn-shake` 类，在待操作项旁添加脉动圆点
- [x] 3.2 实现三步工作流计算属性（step1_done / step2_done / step3_ready），根据步骤状态控制各区域是否可交互
- [x] 3.3 添加物料列表折叠功能（点击标题切换展开/折叠，全部确认后自动折叠）
- [x] 3.4 移除独立的"确认物流单号"按钮，物流图片上传后自动显示"物流已确认"
- [x] 3.5 根据工作流步骤动态调整完成按钮的文案和可用状态
