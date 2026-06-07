## Why

当前编辑物料时，物料编码（`code`）字段不可修改。物料编码是物料的唯一业务标识，在实际使用中可能需要修正（如编码规范变更、录入错误等）。后端 `MaterialUpdate` schema、前端类型定义和编辑表单均未包含 `code` 字段，导致用户无法修改。

## What Changes

- 后端 `MaterialUpdate` schema 新增 `code: Optional[str]` 字段
- 前端 `MaterialUpdate` 类型接口新增 `code?: string` 字段
- 前端物料编辑表单（`MaterialDetail.vue`）新增物料编码输入项

## Capabilities

### New Capabilities
- `edit-material-code`: 编辑物料时允许修改物料编码字段

### Modified Capabilities
<!-- 无现有 specs 需要修改 -->

## Impact

- `app/schemas/__init__.py` — MaterialUpdate schema
- `web/src/types/material.ts` — MaterialUpdate 接口
- `web/src/views/materials/MaterialDetail.vue` — 编辑表单 UI
