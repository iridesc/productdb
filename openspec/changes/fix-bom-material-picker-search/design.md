## Context

`MaterialDetail.vue` 的 BOM 物料选择器使用 Vant UI 的 `van-picker` 组件——一个纯滚动选取列，不支持搜索。相比而言，`ProductSelector.vue` 使用 `van-search` + 滚动列表的成熟模式，已实现搜索和防抖。

本次改动将所有 BOM 物料选择逻辑限制在 `MaterialDetail.vue` 单文件内，不创建新组件。模板结构直接参照 `ProductSelector.vue`，确保 UI 一致性。

## Goals / Non-Goals

**Goals:**
- 将 BOM 物料选择器从 `van-picker` 替换为带 `van-search` 搜索栏的可滚动物料列表
- 支持按名称或编码的服务端搜索，带 300ms 防抖
- 弹窗打开时自动加载物料列表（排除当前物料）
- 显示缩略图、名称、编码和当前库存

**Non-Goals:**
- 不改造 `ProductSelector.vue` 使其更通用
- 不修改后端 API
- 不修改 BOM 编辑/保存逻辑
- 不修改其他页面上的物料选择器（如订单创建页面）

## Decisions

1. **内联实现，不复用 ProductSelector**：BOM 选择器有独特需求——过滤掉当前物料（`m.id !== id`）、无价格列、设置 `material_id`/`material_name` 而非完整产品对象、不同标题。在 `MaterialDetail.vue` 内联实现保持简洁，避免为适应双重上下文而给 `ProductSelector` 增加 props。

2. **服务端搜索，而非客户端过滤**：`fetchMaterials` 之前每次加载 100 条并离线过滤。现在改用 `getMaterials({keyword})` 将搜索委托到服务端，当物料超过 100 条时也能正确工作。

3. **300ms 防抖**：与 `ProductSelector.vue` 中的相同模式——平衡响应速度和 API 调用次数。

4. **弹窗打开时由 watcher 自动加载**：使用 `watch(showMaterialPicker, ...)` 代替手动调用，确保每次打开弹窗时列表都能正确初始化。

## Risks / Trade-offs

- [搜索词未命中] 列表为空时显示 `van-empty`，给出清晰的视觉反馈
- [网络故障] `loadMaterials()` 中的 try/catch 静默失败——与组件内其他加载函数的行为保持一致
- [快速切换搜索词] 防抖取消上一个定时器，防止竞态条件。若上一请求尚未返回，UI 将直接显示最新请求的结果（`materialSearchResults` 被完全替换）

## Open Questions

无——改动范围小而自包含，所有设计要点已明确。
