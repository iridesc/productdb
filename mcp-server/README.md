# ProductDB MCP Server

提供 MCP（Model Context Protocol）服务的 ProductDB 数据查询工具集。使用 [Anthropic MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)（`FastMCP`）构建。

## 架构

```
AI 助手 (MCP Client)
    │  stdio / JSON-RPC 2.0
    ▼
mcp-server/server.py  (Python FastMCP)
    │  HTTP / httpx
    ▼
FastAPI @ localhost:8100  (Docker 容器)
    │
    ▼
PostgreSQL
```

## 前提条件

- Python >= 3.11
- `mcp` 包（Anthropic SDK）已安装
- ProductDB 后端服务已启动（默认 `http://localhost:8100`）

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PRODUCTDB_API_URL` | `http://localhost:8100/api/v1` | FastAPI 地址 |
| `PRODUCTDB_SYSTEM_TOKEN` | 无 | ProductDB 管理员签发的系统 Token（必填） |

## 启动

```bash
cd mcp-server
python -m pip install -r requirements.txt
python server.py
```

MCP Server 启动时会向 ProductDB 校验凭证。缺少 Token，或 Token 无效、被禁用、已过期时，ProductDB 返回 401，MCP Server 随即退出。

## MCP 工具列表

| 工具 | 说明 | 主要参数 |
|------|------|----------|
| `query_materials` | 查询物料列表 | keyword, category, is_active, page, page_size |
| `query_material_categories` | 查询物料分类和子分类 | parent_id |
| `get_material` | 获取物料详情 | id_or_code |
| `get_material_images` | 查询物料图片 | material_id |
| `get_bom` | 查询 BOM 物料清单 | product_id |
| `query_boms` | 查询 BOM 行项目 | product_id, material_id |
| `get_bom_tree` | 查询多层 BOM 树 | product_id |
| `query_inventory` | 查询库存汇总 | category, keyword, low_stock, page |
| `check_inventory` | 查询库存流水 | material_id, transaction_type, page, page_size |
| `get_material_inventory_history` | 查询物料库存历史 | material_id |
| `query_sales_orders` | 查询销售订单 | status, keyword, start_date, end_date, page |
| `get_sales_order` | 获取销售订单详情 | order_id |
| `get_sales_order_images` | 查询销售订单凭证图片 | order_id |
| `publish_sales_order` | 发布销售订单并扣减库存 | order_id, confirm |
| `query_production_orders` | 查询生产订单 | status, keyword, page |
| `get_production_order` | 获取生产订单详情 | order_id |
| `get_production_order_images` | 查询生产订单图片 | order_id |
| `get_production_materials` | 查询生产物料需求和库存 | order_id |
| `publish_production_order` | 发布生产订单并扣减原料 | order_id, confirm |
| `get_dashboard_stats` | 获取系统概览统计 | — |

## 注册到 Codex

在 Codex 桌面端 **Settings → MCP Servers → Add New Server**：

- **Name**: `productdb`
- **Type**: `command`
- **Command**: `python3`
- **Arguments**: `/绝对路径/productdb/mcp-server/server.py`
- **Environment variables**（可选）:
  - `PRODUCTDB_API_URL`: 自定义 API 地址
  - `PRODUCTDB_SYSTEM_TOKEN`: 在 ProductDB 系统 Token 管理中创建的 Token（必填）
