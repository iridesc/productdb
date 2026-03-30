# ERP 物料生产管理系统

基于 FastAPI 的企业资源规划（ERP）系统，支持物料管理、BOM（物料清单）、销售订单、生产订单和库存管理。

## 🚀 功能特性

### 核心模块
- **物料管理**: 支持成品、半成品、原材料、辅料等分类，包含编码、规格、单位、库存等信息
- **BOM 管理**: 产品物料清单，支持多层级递归BOM树，展示完整的物料依赖关系
- **客户管理**: 客户信息维护
- **销售订单**: 销售订单全流程管理（草稿→已确认→生产中→已发货→已完成）
- **生产订单**: 生产订单及自动物料需求计算，库存联动
- **库存管理**: 实时库存查看、库存流水、低库存预警

### 技术特点
- ✅ RESTful API + OpenAPI 文档
- ✅ JWT 认证
- ✅ PostgreSQL 数据库
- ✅ Docker Compose 一键部署
- ✅ 完整的数据校验

## 📦 快速开始

### 前置要求
- Docker
- Docker Compose

### 1. 启动服务

```bash
cd erp-system
docker-compose up -d
```

### 2. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 初始化管理员账号

首次启动后，注册管理员账号：

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 4. 登录获取 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

返回的 `access_token` 用于后续请求：

```bash
curl -X GET "http://localhost:8000/api/v1/materials" \
  -H "Authorization: Bearer <your_token>"
```

## 📚 API 文档

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 登录获取Token |
| POST | /api/v1/auth/register | 注册用户 |

### 物料管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/materials | 物料列表 |
| POST | /api/v1/materials | 创建物料 |
| GET | /api/v1/materials/{id} | 物料详情 |
| PUT | /api/v1/materials/{id} | 更新物料 |
| DELETE | /api/v1/materials/{id} | 删除物料 |

### BOM 管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/boms | BOM列表 |
| POST | /api/v1/boms | 创建BOM项 |
| GET | /api/v1/boms/product/{id} | 获取产品的BOM |
| GET | /api/v1/boms/tree/{id} | 获取BOM树 |
| DELETE | /api/v1/boms/{id} | 删除BOM项 |

### 客户管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/customers | 客户列表 |
| POST | /api/v1/customers | 创建客户 |
| GET | /api/v1/customers/{id} | 客户详情 |
| PUT | /api/v1/customers/{id} | 更新客户 |
| DELETE | /api/v1/customers/{id} | 删除客户 |

### 销售订单
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/sales-orders | 订单列表 |
| POST | /api/v1/sales-orders | 创建订单 |
| GET | /api/v1/sales-orders/{id} | 订单详情 |
| PUT | /api/v1/sales-orders/{id} | 更新订单 |
| PUT | /api/v1/sales-orders/{id}/status | 更新状态 |
| DELETE | /api/v1/sales-orders/{id} | 删除订单 |

### 生产订单
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/production-orders | 生产单列表 |
| POST | /api/v1/production-orders | 创建生产单 |
| GET | /api/v1/production-orders/{id} | 生产单详情 |
| PUT | /api/v1/production-orders/{id}/status | 更新状态 |
| GET | /api/v1/production-orders/{id}/materials | 物料需求 |

### 库存管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/inventory | 库存列表 |
| GET | /api/v1/inventory/transactions | 库存流水 |
| POST | /api/v1/inventory/transactions | 创建库存流水 |
| GET | /api/v1/inventory/{id}/history | 库存历史 |

## 🔧 开发

### 本地开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
uvicorn app.main:app --reload
```

### 数据库迁移

```bash
# 自动创建表（首次启动）
alembic upgrade head
```

## 📁 项目结构

```
erp-system/
├── app/
│   ├── main.py          # FastAPI 应用入口
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库连接
│   ├── models/          # SQLAlchemy 模型
│   ├── schemas/        # Pydantic Schema
│   ├── routers/        # API 路由
│   └── utils/          # 工具函数
├── docker-compose.yml  # Docker Compose 配置
├── Dockerfile          # API 服务镜像
├── requirements.txt    # Python 依赖
├── alembic.ini         # 数据库迁移配置
└── SPEC.md             # 项目规格文档
```

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | postgresql://erp_user:erp_password@localhost:5432/erp_db | 数据库连接 |
| SECRET_KEY | your-secret-key-change-in-production | JWT 密钥 |
| ALGORITHM | HS256 | JWT 算法 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 | Token 过期时间(分钟) |

## 📄 许可证

MIT License