## Context

当前 `SalesOrderDetail.vue` 的工作树中有已修改但未提交的 diff，方向是「物料 → 产品」。这与用户最新决定（全系统统一使用「物料」）相反。需要反转这些改动。

另外，`openspec/specs/sales-order-guided-workflow/spec.md` 原始内容已经使用「material」术语，基本符合新方向，仅需将「product shipping image」「产品图片」等标签更新为「物料图片」。

## Goals / Non-Goals

**Goals:**
- 将销售订单详情页所有面向用户的中文文案统一为「物料」
- 「产品图片/产品发货图片」→「物料图片」
- 同步更新 spec 中的标签描述

**Non-Goals:**
- 不修改后端代码、API、数据模型
- 不修改数据库枚举值 `product_shipping`（保持 `SalesOrderImageType.product_shipping`）
- 不修改变量名（如 `productShippingImages`、`products` 等），仅改用户可见文案

## Decisions

1. **纯文案替换，方向反转** — 将工作树中「物料→产品」的改动全部反转，改为统一使用「物料」。`product_shipping` 枚举值保持不动，只改 UI 中文标签。

2. **工作流标签方案**：
   - Step 1: 「检查物料」→「物料已检查」
   - Step 2: 「物料图片」→「物料图已上传」
   - Step 3: 「物流图片」→「物流已确认」（不变）

3. **不改变量名** — `productShippingImages`、`filteredProducts`、`productImageInputRef` 等 JS 变量名保持不变，重构留待后续。

## Risks / Trade-offs

- **风险**: 极低。纯文案变更，不影响功能和数据结构。
- **回滚**: `git checkout` 即可。
