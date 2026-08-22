## Why

在 `MaterialDetail.vue` 页面中添加 BOM 项时，选择物料的弹窗使用的是 Vant UI 的 `van-picker` 组件。该组件是纯滚动选择器，不支持搜索功能。当系统中物料数量较多时（可能上百个），用户必须手动滚动浏览所有物料才能找到目标，严重影响操作效率。

## What Changes

- 将 `MaterialDetail.vue` 中 BOM 添加/编辑时的物料选择器从 `van-picker`（纯滚动选择）替换为带 `van-search` 搜索栏的列表选择界面，支持按物料名称或编码实时搜索过滤
- `fetchMaterials` 函数改为支持传入关键词进行服务端搜索，而非仅在前端对已加载的100条数据进行过滤

## Capabilities

### New Capabilities
- `bom-material-search`: BOM 物料选择器支持搜索功能，用户可以通过关键词快速查找物料

### Modified Capabilities
<!-- None: this is a new capability, not modifying existing spec requirements -->

## Impact

- 前端文件：`web/src/views/materials/MaterialDetail.vue` — 替换物料选择弹窗的 UI 实现
