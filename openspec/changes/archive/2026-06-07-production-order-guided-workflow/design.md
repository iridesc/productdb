## Context

生产订单当前仅有基础的发布/完成按钮和 van-tag 状态。需要全面对齐销售订单的引导式工作流模式，并增加产出实物留证和真实产量确认。

## Goals / Non-Goals

**Goals:**
- 四步引导式工作流：检查物料 → 确认产出 → 上传产品图 → 完成
- 新增 `ProductionOrderImage` 模型（仅 `product_shipping` 一种类型）
- 新增「确认产出数量」步骤，生产人员输入真实产出数量存入 `completed_quantity`
- 物料列表可折叠，与产品图上传统分卡独立

**Non-Goals:**
- 不上传物流/凭证图
- 物料与产品图不合并在同一卡片

## Decisions

### 1. 数据模型：`ProductionOrderImage`

结构同 `SalesOrderImage`，`image_type` 固定为 `product_shipping`（产品产出图）。

### 2. 四步工作流

```
① 检查物料     → consumed_quantity = quantity 逐个标记
② 确认产出数量 → completed_quantity 设置为真实产出数（≤计划数）
③ 上传产品图   → 至少1张 product_shipping 图片
④ 完成生产     → 全部满足后按钮可用
```

### 3. 产出数量确认

新增 `PUT /production-orders/{id}/yield` 端点，接收 `completed_quantity`。
前端在步骤②显示输入框 + 确认按钮，默认值 = 订单计划数量。

### 4. 前端布局

```
进度条（顶部）
├ 订单信息卡片
├ 物料需求卡片（可折叠，逐个检查按钮）
├ 产出数量确认卡片
├ 产品图上传卡片
└ 完成/取消按钮
```

不合并物料与产品图。
