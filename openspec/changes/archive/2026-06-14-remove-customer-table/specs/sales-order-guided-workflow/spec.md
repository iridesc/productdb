## MODIFIED Requirements

### Requirement: 销售订单使用 customer_info 自由文本字段

销售订单的客户信息 SHALL 使用单一的 `customer_info` 自由文本字段，替代原有的 `customer_id`（外键关联客户表）+ `customer_name` + `customer_address` 组合。

系统 SHALL NOT 将客户作为独立实体管理，不应当存在客户表或客户 CRUD API。

#### Scenario: 创建销售订单时填写客户信息

- **WHEN** 用户创建销售订单并填写客户信息
- **THEN** 系统将 `customer_info` 作为自由文本字符串保存到销售订单
- **AND** `customer_info` 字段可包含客户名称、电话、地址等任意收货信息

#### Scenario: 查看销售订单详情时展示客户信息

- **WHEN** 用户查看销售订单详情
- **THEN** 订单信息中展示 `customer_info` 的完整文本内容

#### Scenario: 编辑销售订单时修改客户信息

- **WHEN** 用户编辑销售订单
- **THEN** 可以修改 `customer_info` 字段的文本内容

#### Scenario: 列表页展示客户信息

- **WHEN** 用户查看销售订单列表
- **THEN** 每条订单的客户信息列展示 `customer_info` 的值，空值时显示 "-"
