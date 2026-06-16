## 1. 前端实现

- [x] 1.1 在 `SalesOrderList.vue` 表格 `<thead>` 中新增「备注」列标题
- [x] 1.2 在 `<tbody>` 每行新增备注列 `<td>`，展示 `item.remark || '-'`
- [x] 1.3 为备注列和客户信息列添加 CSS 截断样式（`max-width` + `text-overflow: ellipsis`）
- [x] 1.4 添加 `showFullText` 函数，使用 `showDialog` 弹窗展示完整文本
- [x] 1.5 备注和客户信息列绑定 `@click` 事件，有内容时可点击弹窗

## 2. 验证

- [x] 2.1 创建一条有长备注的销售订单，验证列表截断+弹窗
- [x] 2.2 验证客户信息过长时截断+弹窗
- [x] 2.3 验证空备注/空客户信息显示 "-" 且不可点击
