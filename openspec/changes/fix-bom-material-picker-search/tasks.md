## 1. 替换脚本状态和函数（MaterialDetail.vue）

- [x] 1.1 替换 ref 声明：移除 `materialOptions` 和 `allMaterials`，添加 `materialSearchKeyword`、`materialListLoading`、`materialSearchResults`、`searchTimer`
- [x] 1.2 删除 `fetchMaterials()` 函数，添加 `loadMaterials(keyword?)`（服务端搜索）和 `handleMaterialSearch(value)`（300ms 防抖）函数
- [x] 1.3 添加 `watch(showMaterialPicker, ...)` 在弹窗打开时自动加载物料列表并清除搜索关键词
- [x] 1.4 删除 `onMaterialConfirm()` 函数，添加 `selectMaterial(material)` 函数（直接设置 `material_id` 和 `material_name`）
- [x] 1.5 从 `openAddBOM()` 和 `handleEdit()` 中移除对已删除的 `fetchMaterials()` 的调用

## 2. 替换模板中的物料选择器

- [x] 2.1 将 `van-picker` 弹窗替换为带 `van-search` 搜索栏和 `van-loading`/`van-empty` 状态的自定义可滚动物料列表
- [x] 2.2 每个物料项显示缩略图（或占位符）、名称、编码和当前库存

## 3. 添加 CSS 样式

- [x] 3.1 在 `<style scoped>` 中添加物料选择器弹窗样式（picker-header、product-list-container、product-item、product-item-thumb、product-item-info、product-item-code、product-item-stock、loading-center）

## 4. 验证

- [ ] 4.1 验证 BOM 物料选择器打开时自动加载物料列表
- [ ] 4.2 验证搜索栏输入关键词能正确过滤物料
- [ ] 4.3 验证选择物料后正确填充到 BOM 表单
- [ ] 4.4 验证当前物料不出现在可选列表中
