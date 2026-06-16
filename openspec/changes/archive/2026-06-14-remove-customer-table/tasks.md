## 1. 数据模型变更

- [x] 1.1 在 `app/models/transaction.py` 中删除 `Customer` 类定义
- [x] 1.2 在 `app/models/transaction.py` 中删除 `SalesOrder` 的 `customer_id`、`customer_name`、`customer_address` 字段
- [x] 1.3 在 `app/models/transaction.py` 中为 `SalesOrder` 添加 `customer_info = Column(Text, nullable=True)` 字段
- [x] 1.4 删除 `SalesOrder.customer` relationship
- [x] 1.5 更新 `app/models/__init__.py`，移除 `Customer` 导出

## 2. Schema 变更

- [x] 2.1 在 `app/schemas/__init__.py` 中删除 `CustomerBase`、`CustomerCreate`、`CustomerUpdate`、`CustomerResponse`、`CustomerListResponse`
- [x] 2.2 在 `app/schemas/__init__.py` 中修改 `SalesOrderBase`/`SalesOrderCreate`/`SalesOrderUpdate`：移除 `customer_id`、`customer_name`、`customer_address`，添加 `customer_info: Optional[str]`
- [x] 2.3 在 `app/schemas/__init__.py` 中修改 `SalesOrderResponse`：移除 `customer: Optional[CustomerResponse]`，替换为 `customer_info: Optional[str]`

## 3. 后端 API

- [x] 3.1 删除 `app/routers/customer.py` 文件
- [x] 3.2 在 `app/routers/__init__.py` 和 `app/main.py` 中移除 customer router 的注册
- [x] 3.3 修改 `app/routers/sales_order.py`：移除 `Customer` 导入，移除创建/更新订单中的 `customer_id` 查找逻辑，改为直接使用 `customer_info`
- [x] 3.4 修改 `app/routers/sales_order.py` 中列表查询：移除 `customer_id` 筛选参数，移除 `Customer.name`/`Customer.contact` 关键词搜索

## 4. 数据库迁移

- [x] 4.1 编写 migration SQL：`ALTER TABLE sales_orders ADD COLUMN customer_info TEXT`
- [x] 4.2 编写数据迁移 SQL：`UPDATE sales_orders SET customer_info = TRIM(COALESCE(customer_name, '') || ' ' || COALESCE(customer_address, ''))`
- [x] 4.3 编写清理 SQL：`ALTER TABLE sales_orders DROP COLUMN customer_id, DROP COLUMN customer_name, DROP COLUMN customer_address; DROP TABLE IF EXISTS customers`
- [x] 4.4 在容器启动脚本或 `app/main.py` 的 lifespan 中集成迁移执行

## 5. 前端类型

- [x] 5.1 在 `web/src/types/sales.ts` 中更新 `SalesOrder`：移除 `customer_id`、`customer_name`、`customer_address`，添加 `customer_info?: string`
- [x] 5.2 在 `web/src/types/sales.ts` 中更新 `SalesOrderCreate` 和 `SalesOrderUpdate`：同样替换为 `customer_info`

## 6. 前端页面

- [x] 6.1 修改 `web/src/views/sales/SalesOrderCreate.vue`：将 `customer_name` 输入框替换为 `customer_info` 多行文本输入框（textarea）
- [x] 6.2 修改 `web/src/views/sales/SalesOrderList.vue`：`item.customer_name` → `item.customer_info`
- [x] 6.3 修改 `web/src/views/sales/SalesOrderDetail.vue`：展示 `customer_info` 替代原有客户名称

## 7. 验证

- [x] 7.1 启动应用，验证 `Base.metadata.create_all` 正确创建新表结构（无 customers 表，sales_orders 有 customer_info 列）
- [x] 7.2 测试创建销售订单时填写 customer_info
- [x] 7.3 测试编辑销售订单时修改 customer_info
- [x] 7.4 测试销售订单列表和详情页正确展示 customer_info
- [x] 7.5 确认客户管理 API 端点已完全移除（访问 `/customers` 返回 404）
