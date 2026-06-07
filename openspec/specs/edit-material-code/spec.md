# Edit Material Code

**Purpose:** Allow users to modify the material code (`code` field) when editing a material.

## Requirements

### Requirement: User can edit material code
用户在编辑物料时 SHALL 能够修改物料编码（`code`）字段。

#### Scenario: Edit material code successfully
- **WHEN** 用户在物料详情页进入编辑模式，修改物料编码为新的唯一值并保存
- **THEN** 系统更新该物料的 `code` 字段，返回更新后的物料信息

#### Scenario: Duplicate material code rejected
- **WHEN** 用户修改物料编码为数据库中已存在的编码值并保存
- **THEN** 系统返回错误提示，告知编码已存在，物料编码保持不变

#### Scenario: Edit other fields without changing code
- **WHEN** 用户编辑物料的其他字段（如名称、价格）但不修改物料编码
- **THEN** 系统正常更新其他字段，物料编码保持原值不变（`code` 为 Optional，不传时不更新）
