# ERP 物料生产管理系统 - 技术设计文档

## 文档信息

- 版本：1.0
- 日期：2026-03-28
- 状态：需求确认

---

## 一、系统概述

### 1.1 项目背景

本系统为制造业、组装型企业提供物料管理、生产订单、销售订单的完整解决方案。

### 1.2 技术栈

| 技术 | 选择 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| 认证 | JWT |
| 部署 | Docker Compose |
| API 文档 | Swagger UI + ReDoc |

---

## 二、功能模块

### 2.1 产品/物料管理

#### 2.1.1 物料属性

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 是 | 主键 |
| code | String(50) | 是 | 唯一编码 |
| name | String(100) | 是 | 名称 |
| specification | String(200) | 否 | 规格型号 |
| unit | String(20) | 是 | 单位（个、箱等） |
| price | Decimal | 否 | 销售单价 |
| current_stock | Decimal | 是 | 当前库存（默认0） |
| safety_stock | Decimal | 否 | 安全库存 |
| description | Text | 否 | 描述 |
| is_active | Boolean | 是 | 是否启用 |
| created_at | DateTime | 是 | 创建时间 |
| updated_at | DateTime | 是 | 更新时间 |

#### 2.1.2 标签功能

- 管理员可自定义创建标签
- 标签可分配给任意物料
- 一个物料可打多个标签
- 标签支持新增、修改、删除

#### 2.1.3 BOM（物料清单）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | UUID | 是 | 主键 |
| product_id | UUID | 是 | 产品ID（父级） |
| material_id | UUID | 是 | 物料ID（子级） |
| quantity | Decimal | 是 | 数量 |
| is_optional | Boolean | 是 | 是否可选 |

**BOM 特性**：
- 物料可以是产品（递归组成）或原材料
- 递归展示多层级的物料依赖

---

### 2.2 销售订单

#### 2.2.1 流程图

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   草稿      │───▶│   已发布    │───▶│   进行中    │───▶│   已完成    │
│  销售人员    │    │ 发货人员    │    │ 发货人员    │    │             │
│ 创建+添加   │    │             │    │ 逐个确认    │    │             │
│ 填快递单号  │    │             │    │ +确认快递   │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │   已取消    │
                                        └─────────────┘
```

#### 2.2.2 状态说明

| 状态 | 操作者 | 说明 |
|------|--------|------|
| 草稿 | 销售人员 | 创建订单、添加商品、添加客户、填写快递单号 |
| 已发布 | 发货人员 | 等待发货 |
| 进行中 | 发货人员 | 逐个确认商品（扣减库存）、确认快递单号 |
| 已完成 | - | 订单完成 |
| 已取消 | - | 订单取消（不可撤回） |

#### 2.2.3 业务规则

**发布规则**：
- 快递单号必填
- 所有商品库存充足

**发货规则**：
- 每个商品单独点击"确认" → 扣减库存
- 确认快递单号
- 点击"完成"前校验：所有商品已确认 + 快递单号已确认

**取消规则**：
- 已发布订单可取消
- 取消后不可撤回

#### 2.2.4 数据模型

**销售订单**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_no | String(20) | 订单号（自动生成） |
| customer_id | UUID | 客户ID |
| customer_name | String | 客户名称（冗余） |
| customer_address | String | 客户地址 |
| express_no | String | 快递单号（草稿阶段必填） |
| status | Enum | 状态 |
| total_amount | Decimal | 总金额 |
| remark | Text | 备注 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**销售订单明细**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_id | UUID | 订单ID |
| product_id | UUID | 产品ID |
| product_name | String | 产品名称（冗余） |
| quantity | Decimal | 数量 |
| unit_price | Decimal | 单价 |
| amount | Decimal | 金额 |
| is_confirmed | Boolean | 是否已确认（发货用） |
| created_at | DateTime | 创建时间 |

---

### 2.3 生产订单

#### 2.3.1 流程图

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   草稿      │───▶│   已发布    │───▶│   进行中    │───▶│   已完成    │
│ 创建+选择   │    │ 检查库存    │    │ 逐个分配    │    │ 校验+成品   │
│ 产品+数量   │    │ 充足才能    │    │ 库存扣减    │    │ 入库        │
│ 显示BOM    │    │ 发布       │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │   已取消    │
                                        └─────────────┘
```

#### 2.3.2 状态说明

| 状态 | 操作者 | 说明 |
|------|--------|------|
| 草稿 | 创建者 | 选择产品、填写数量、显示BOM物料 |
| 已发布 | 生产人员 | 等待生产 |
| 进行中 | 生产人员 | 逐个分配物料（扣减库存） |
| 已完成 | - | 成品已入库 |
| 已取消 | - | 订单取消 |

#### 2.3.3 业务规则

**发布规则**：
- 检查所有 BOM 物料库存是否充足

**生产规则**：
- 每个 BOM 物料单独点击"分配库存" → 逐个扣减

**完成规则**：
- 校验所有 BOM 物料已分配完成
- 生成成品库存（数量 = 生产数量）

**取消规则**：
- 已发布订单可取消
- 取消后不可撤回

#### 2.3.4 数据模型

**生产订单**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_no | String(20) | 生产单号（自动生成） |
| product_id | UUID | 产品ID |
| product_name | String | 产品名称（冗余） |
| quantity | Decimal | 生产数量 |
| status | Enum | 状态 |
| remark | Text | 备注 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**生产订单物料明细**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| order_id | UUID | 订单ID |
| material_id | UUID | 物料ID |
| material_name | String | 物料名称（冗余） |
| quantity | Decimal | 需求数量 |
| is_distributed | Boolean | 是否已分配库存 |
| created_at | DateTime | 创建时间 |

---

### 2.4 库存管理

#### 2.4.1 功能

- 实时库存查看
- 库存流水记录
- 低库存预警（低于安全库存）
- 手动库存调整

#### 2.4.2 库存变化场景

| 场景 | 库存变化 |
|------|----------|
| 销售订单-商品确认 | 扣减 |
| 生产订单-物料分配 | 扣减 |
| 生产订单-完成 | 增加成品 |
| 手动调整 | 增加/减少 |

---

## 三、API 接口设计

### 3.1 认证模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 登录 |
| POST | /api/v1/auth/register | 注册 |

### 3.2 物料/产品模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/materials | 物料列表（支持分类、标签搜索） |
| POST | /api/v1/materials | 创建物料 |
| GET | /api/v1/materials/{id} | 物料详情 |
| PUT | /api/v1/materials/{id} | 更新物料 |
| DELETE | /api/v1/materials/{id} | 删除物料 |

### 3.3 标签模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tags | 标签列表 |
| POST | /api/v1/tags | 创建标签 |
| PUT | /api/v1/tags/{id} | 更新标签 |
| DELETE | /api/v1/tags/{id} | 删除标签 |

### 3.4 BOM 模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/boms | BOM列表 |
| POST | /api/v1/boms | 创建BOM项 |
| GET | /api/v1/boms/product/{id} | 获取产品的BOM |
| GET | /api/v1/boms/tree/{id} | 获取BOM树（递归） |
| DELETE | /api/v1/boms/{id} | 删除BOM项 |

### 3.5 销售订单模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/sales-orders | 订单列表 |
| POST | /api/v1/sales-orders | 创建订单（草稿） |
| GET | /api/v1/sales-orders/{id} | 订单详情 |
| PUT | /api/v1/sales-orders/{id} | 更新订单 |
| PUT | /api/v1/sales-orders/{id}/publish | 发布订单 |
| PUT | /api/v1/sales-orders/{id}/items/{item_id}/confirm | 确认商品 |
| PUT | /api/v1/sales-orders/{id}/confirm-express | 确认快递单号 |
| PUT | /api/v1/sales-orders/{id}/complete | 完成订单 |
| PUT | /api/v1/sales-orders/{id}/cancel | 取消订单 |

### 3.6 生产订单模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/production-orders | 生产单列表 |
| POST | /api/v1/production-orders | 创建生产单（草稿） |
| GET | /api/v1/production-orders/{id} | 生产单详情 |
| PUT | /api/v1/production-orders/{id}/publish | 发布生产单 |
| PUT | /api/v1/production-orders/{id}/items/{item_id}/distribute | 分配物料库存 |
| PUT | /api/v1/production-orders/{id}/complete | 完成生产单 |
| PUT | /api/v1/production-orders/{id}/cancel | 取消生产单 |

### 3.7 库存模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/inventory | 库存列表 |
| GET | /api/v1/inventory/{id} | 物料库存详情 |
| GET | /api/v1/inventory/transactions | 库存流水 |
| POST | /api/v1/inventory/adjust | 手动调整库存 |

---

## 四、数据字典

### 4.1 销售订单状态

| 状态值 | 说明 |
|--------|------|
| draft | 草稿 |
| published | 已发布 |
| in_progress | 进行中 |
| completed | 已完成 |
| cancelled | 已取消 |

### 4.2 生产订单状态

| 状态值 | 说明 |
|--------|------|
| draft | 草稿 |
| published | 已发布 |
| in_progress | 进行中 |
| completed | 已完成 |
| cancelled | 已取消 |

---

## 五、非功能需求

### 5.1 性能要求

- API 响应时间 < 1s（正常负载下）
- 支持 100 并发用户

### 5.2 安全要求

- 所有 API（除登录外）需认证
- 密码加密存储
- JWT Token 认证

### 5.3 部署要求

- Docker Compose 一键部署
- PostgreSQL 数据持久化

---

## 六、数据存储

### 6.1 PostgreSQL 数据库

- 所有业务数据存储在 PostgreSQL
- 数据库名称：erp_db
- 自动创建数据库和表
- **备份功能：待实现**

---

## 七、产品图片

### 7.1 功能

- 每个产品可上传多张图片
- 支持 JPEG、PNG 格式
- 支持图片预览、删除
- **图片直接存储在 PostgreSQL 数据库中**（bytea 类型）

### 7.2 数据模型

**产品图片**：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| material_id | UUID | 物料ID |
| image_data | Bytea | 图片二进制数据（存储在DB） |
| image_type | String | 图片 MIME 类型（image/jpeg, image/png） |
| filename | String | 文件名 |
| sort_order | Integer | 排序（越小越靠前） |
| created_at | DateTime | 上传时间 |

### 7.3 存储方式

- 图片以二进制形式（bytea）直接存入 PostgreSQL
- 优点：数据统一管理，无需额外存储服务
- 限制：单张图片建议 < 1MB

---

## 八、前端设计

### 8.1 设计原则

- **简洁**：没有多余的元素和复杂的逻辑
- **直观**：操作流程清晰，用户一眼就能看懂
- **友好**：手机端和电脑端都能良好展示

### 8.2 PWA 应用

- 渐进式 Web 应用（PWA）
- 可从浏览器直接安装到手机桌面
- 支持离线使用（基础功能）
- 响应式设计，适配各种屏幕尺寸

### 8.3 技术栈（前端）

- 框架：Vue 3 + TypeScript
- UI 组件库：Element Plus 或 Vant
- 构建工具：Vite
- PWA：Vite PWA 插件

---

## 九、API 接口设计原则

- 语义化：URL 和 HTTP 方法表达清晰
- RESTful：遵循 REST 风格
- 统一响应格式：{ code, message, data }
- 详细错误信息：便于排查问题

---

## 十、项目结构

```
erp-system/
├── app/                  # 后端 API
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   └── utils/
├── web/                  # 前端 Web
│   ├── src/
│   ├── public/
│   ├── index.html
│   └── vite.config.ts
├── backups/              # 数据库备份
├── docker-compose.yml    # Docker 部署
├── Dockerfile            # API 镜像
├── Dockerfile.web        # Web 镜像
├── requirements.txt
└── DESIGN.md
```

---

## 十一、待定事项

1. 图片存储方案（本地 vs 对象存储）
2. 备份策略具体配置
3. 前端 UI 细节确认

---

*文档结束*