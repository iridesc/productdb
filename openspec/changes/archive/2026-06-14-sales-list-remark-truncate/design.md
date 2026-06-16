## Context

当前 `SalesOrderList.vue` 使用 HTML table 展示销售订单列表，共 7 列：订单号、图片、状态、客户、金额、商品数、创建时间。缺少备注列，且客户信息可能很长。

## Goals / Non-Goals

**Goals:**
- 添加备注列
- 备注和客户信息列实现 CSS 截断 + 点击弹窗

**Non-Goals:**
- 不改变其他列的行为
- 不添加后端接口

## Decisions

### 截断方案

使用 CSS 类实现文本截断：
```css
.text-ellipsis {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

### 弹窗方案

使用 Vant 的 `showDialog`（`van-dialog` 的 imperative API）直接弹出，无需额外组件：
```ts
import { showDialog } from 'vant'
function showFullText(title: string, text: string) {
  showDialog({ title, message: text, confirmButtonText: '关闭' })
}
```

有内容的列才可点击，空值显示 "-" 不可点击。
