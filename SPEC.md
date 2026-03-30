# ERP 物料生产管理系统 - 项目规格

## 1. 项目概述

- **项目名称**: productdb
- **类型**: RESTful API 后端服务
- **核心功能**: 物料管理、产品BOM、生产订单、销售订单的ERP系统
- **目标用户**: 制造业、组装企业

## 2. 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT
- **部署**: Docker Compose

## 3. 核心数据模型

### 3.1 物料 (Material)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| code | String(50) | 物料编码（唯一） |
| name | String(100) | 物料名称 |
| category | Enum | 分类：成品/半成品/原材料/辅料 |
| unit | String(20) | 单位 |
| specification | String(200) | 规格型号 |
| safety_stock | Decimal | 安全库存 |
| current_stock | Decimal | 当前库存 |
| price | Decimal | 单价 |
| description | Text | 描述 |
| is_active | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 3.2 物料分类 (MaterialCategory)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | String(50) | 分类名称 |
| code | String(20) | 分类编码 |
| parent_id | UUID | 父分类ID |

### 3.3 BOM (物料清单) (BOM)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| product_id | UUID | 成品ID |
| material_id | UUID | 物料ID |
| quantity | Decimal | 用量 |
| scrap_rate | Decimal | 损耗率(%) |
| is_optional | Boolean | 是否可选 |

### 3.4 销售订单 (SalesOrder)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_no | String(20) | 订单号 |
| customer_id | UUID | 客户ID |
| order_date | Date | 订单日期 |
| delivery_date | Date | 交货日期 |
| status | Enum | 状态 |
| total_amount | Decimal | 总金额 |
| remark | Text | 备注 |

### 3.5 销售订单明细 (SalesOrderItem)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_id | UUID | 订单ID |
| product_id | UUID | 产品ID |
| quantity | Decimal | 数量 |
| unit_price | Decimal | 单价 |
| amount | Decimal | 金额 |

### 3.6 生产订单 (ProductionOrder)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_no | String(20) | 生产单号 |
| sales_order_id | UUID | 关联销售订单 |
| product_id | UUID | 产品ID |
| quantity | Decimal | 生产数量 |
| start_date | Date | 计划开始日期 |
| end_date | Date | 计划结束日期 |
| status | Enum | 状态 |
| remark | Text | 备注 |

### 3.7 客户 (Customer)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | String(100) | 客户名称 |
| code | String(20) | 客户编码 |
| contact | String(50) | 联系人 |
| phone | String(20) | 电话 |
| address | String(200) | 地址 |
| is_active | Boolean | 是否启用 |

## 4. API 接口

### 4.1 认证
- POST /api/v1/auth/login - 登录
- POST /api/v1/auth/refresh - 刷新Token

### 4.2 物料管理
- GET /api/v1/materials - 物料列表
- POST /api/v1/materials - 创建物料
- GET /api/v1/materials/{id} - 物料详情
- PUT /api/v1/materials/{id} - 更新物料
- DELETE /api/v1/materials/{id} - 删除物料

### 4.3 物料分类
- GET /api/v1/material-categories - 分类列表
- POST /api/v1/material-categories - 创建分类

### 4.4 BOM管理
- GET /api/v1/boms - BOM列表
- POST /api/v1/boms - 创建BOM
- GET /api/v1/boms/{product_id} - 获取产品的BOM
- DELETE /api/v1/boms/{id} - 删除BOM项

### 4.5 客户管理
- GET /api/v1/customers - 客户列表
- POST /api/v1/customers - 创建客户

### 4.6 销售订单
- GET /api/v1/sales-orders - 订单列表
- POST /api/v1/sales-orders - 创建订单
- GET /api/v1/sales-orders/{id} - 订单详情
- PUT /api/v1/sales-orders/{id} - 更新订单
- PUT /api/v1/sales-orders/{id}/status - 更新状态

### 4.7 生产订单
- GET /api/v1/production-orders - 生产单列表
- POST /api/v1/production-orders - 创建生产单
- GET /api/v1/production-orders/{id} - 生产单详情
- PUT /api/v1/production-orders/{id}/status - 更新状态

### 4.8 库存
- GET /api/v1/inventory - 库存列表
- POST /api/v1/inventory/transactions - 库存流水

## 5. 部署结构

```
productdb/
├── docker-compose.yml
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   └── utils/
├── alembic/
└── README.md
```

## 6. 环境变量

- DATABASE_URL: PostgreSQL连接字符串
- SECRET_KEY: JWT密钥
- ALGORITHM: JWT算法
- ACCESS_TOKEN_EXPIRE_MINUTES: Token过期时间