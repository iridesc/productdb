## 1. Database

- [x] 1.1 `users` 表新增 `can_create_sales BOOLEAN DEFAULT false`
- [x] 1.2 `users` 表新增 `can_create_production BOOLEAN DEFAULT false`
- [x] 1.3 更新现有超级管理员用户，设置两个新字段为 true

## 2. Backend

- [x] 2.1 `User` 模型新增两列
- [x] 2.2 `UserBase` schema 新增两字段（默认 false）
- [x] 2.3 `UserUpdate` schema 新增两字段（Optional）
- [x] 2.4 `POST /users` 创建用户时保存新字段
- [x] 2.5 `PUT /users/{id}` 更新用户时处理新字段
- [x] 2.6 `POST /auth/login` 响应中包含新字段

## 3. Frontend

- [x] 3.1 `User` 类型定义新增两字段
- [x] 3.2 用户创建表单新增「可创建销售订单」「可创建生产订单」开关
- [x] 3.3 用户编辑表单新增对应开关
- [x] 3.4 `SalesOrderList` plus 按钮加 `v-if="canCreate"`（检查 `can_create_sales`）
- [x] 3.5 `SalesOrderCreate` 页权限门控改为检查 `can_create_sales`
- [x] 3.6 `ProductionOrderList` plus 按钮加 `v-if="canCreate"`（检查 `can_create_production`）
- [x] 3.7 `ProductionOrderCreate` 页权限门控改为检查 `can_create_production`
- [x] 3.8 `MaterialDetail`「创建生产订单」按钮改为检查 `can_create_production`

## 4. Deploy

- [x] 4.1 前端构建 + 后端镜像重建 + 全部署
