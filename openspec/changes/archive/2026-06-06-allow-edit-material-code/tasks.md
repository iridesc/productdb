## 1. 后端 Schema 修改

- [x] 1.1 `app/schemas/__init__.py` — `MaterialUpdate` 类新增 `code: Optional[str] = None` 字段

## 2. 前端类型修改

- [x] 2.1 `web/src/types/material.ts` — `MaterialUpdate` 接口新增 `code?: string` 字段

## 3. 前端编辑表单修改

- [x] 3.1 `web/src/views/materials/MaterialDetail.vue` — 编辑表单 `form` 对象新增 `code` 字段，并在模板中紧挨 `name` 输入框之后添加物料编码的 `van-field` 输入项
