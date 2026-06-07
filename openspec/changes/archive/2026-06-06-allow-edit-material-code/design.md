## Context

物料编辑（PUT `/materials/{id}`）已支持修改名称、分类、单位、规格、库存、价格等字段，但物料编码（`code`）被遗漏。`code` 字段存在于 `Material` 模型和数据库表中，前端的 `Material` 接口也有 `code`，但 `MaterialUpdate` schema（前后端）和编辑表单均未包含。

后端 `update_material` 使用通用的 `setattr` 按 key 赋值，因此只需在 schema 中加字段即可自动生效，无需修改路由逻辑。

## Goals / Non-Goals

**Goals:**
- 编辑物料时允许修改 `code` 字段
- 保持与其他字段一致的交互体验

**Non-Goals:**
- 不涉及物料编码的唯一性校验（已有 DB 约束）——此变更只是暴露字段给用户编辑
- 不涉及创建物料流程（创建时已支持填写 code）

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 后端 schema 字段位置 | `MaterialUpdate.code: Optional[str] = None` | 与其他字段风格一致，Optional 保证向后兼容 |
| 前端表单位置 | 放在名称（name）之后，第一屏可见 | 编码是核心标识，应与名称相邻 |
| 是否需要额外校验 | 不需要，依赖后端 DB unique 约束报错 | 保持简单，DB 已有 `unique=True` |

## Risks / Trade-offs

- **[误操作风险]** 用户可能无意中修改了正在被其他订单引用的物料编码 → **缓解**: 编码修改后，关联的生产订单/销售订单通过 `product_id`（UUID）关联，不依赖 `code`，不会破坏关联关系
- **[唯一性冲突]** 用户输入已存在的编码 → **缓解**: DB unique 约束会抛异常，后端返回 400 错误提示
