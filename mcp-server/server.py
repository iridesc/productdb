#!/usr/bin/env python3
"""
ProductDB MCP Server

Exposes ProductDB data (materials, BOM, orders, inventory) as MCP tools
so that AI assistants can query them naturally.
Uses Anthropic's official MCP Python SDK (FastMCP).

Usage:
    python server.py

Environment:
    PRODUCTDB_API_URL     FastAPI base URL (default: http://localhost:8100/api/v1)
    PRODUCTDB_SYSTEM_TOKEN administrator-issued system token (required)
"""

import os
import sys
import asyncio
from mcp.server.fastmcp import FastMCP

try:
    # 作为包被集成进 app（容器内）时
    from mcp_server.client import get_client
except ImportError:
    # 直接运行 mcp-server/server.py 时
    from client import get_client

mcp = FastMCP("ProductDB")


# ====================================================================
# Helper — pretty-print a list of dicts as a table
# ====================================================================

def _table(items: list[dict], fields: list[str]) -> str:
    if not items:
        return "(empty)"

    def _val(item, field):
        v = item.get(field)
        if v is None:
            return "-"
        if isinstance(v, float):
            return f"{v:.2f}"
        if isinstance(v, dict):
            return v.get("name") or v.get("label") or v.get("code") or str(v)
        return str(v)

    rows = [{f: _val(r, f) for f in fields} for r in items]

    def _width(s):
        return sum(2 if ord(c) > 0x7f else 1 for c in s)

    widths = [max(_width(f), max(_width(r[f]) for r in rows)) for f in fields]

    head = "  ".join(f.ljust(w) for f, w in zip(fields, widths))
    sep  = "──".join("─" * w for w in widths)
    body = "\n".join(
        "  ".join(r[f].ljust(w) for f, w in zip(fields, widths))
        for r in rows
    )
    return f"{head}\n{sep}\n{body}"


def _flatten(obj, indent=0) -> str:
    """Pretty-print a nested dict/list as indented text."""
    pad = "  " * indent
    lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if v is None:
                continue
            if isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}:")
                lines.append(_flatten(v, indent + 1))
            elif isinstance(v, bool):
                lines.append(f"{pad}{k}: {'yes' if v else 'no'}")
            elif isinstance(v, float):
                lines.append(f"{pad}{k}: {v:.2f}")
            else:
                lines.append(f"{pad}{k}: {v}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, dict):
                lines.append(f"{pad}[{i}]")
                lines.append(_flatten(item, indent + 1))
            else:
                lines.append(f"{pad}- {item}")
    else:
        lines.append(f"{pad}{obj}")
    return "\n".join(lines)


# ====================================================================
# MCP Tools (async — 同步 httpx 会阻塞事件循环导致容器内自调用死锁)
# ====================================================================

@mcp.tool(
    name="query_materials",
    description="搜索/查询物料列表，支持按名称、编码、类别筛选和分页",
)
async def query_materials(
    keyword: str | None = None,
    category: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> str:
    cli = get_client()
    data = await cli.query_materials(
        keyword=keyword,
        category=category,
        is_active=is_active,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items = data if isinstance(data, list) else data.get("items", [])
    return _table(
        items,
        ["id", "code", "name", "category", "current_stock", "unit", "price", "sale_price"],
    )


@mcp.tool(
    name="query_material_categories",
    description="查询物料分类；不传 parent_id 时返回顶级分类，传入后返回其子分类",
)
async def query_material_categories(parent_id: str | None = None) -> str:
    data = await get_client().query_material_categories(parent_id=parent_id)
    return _table(data, ["id", "code", "name", "parent_id", "created_at"])


@mcp.tool(
    name="get_material",
    description="获取单个物料的完整信息（含关联数据）",
)
async def get_material(id_or_code: str) -> str:
    cli = get_client()
    data = await cli.get_material(id_or_code)
    return _flatten(data)


@mcp.tool(
    name="get_material_images",
    description="查询指定物料的图片元数据和访问地址",
)
async def get_material_images(material_id: str) -> str:
    data = await get_client().get_material_images(material_id)
    return _table(data, ["id", "image_url", "sort_order", "created_at"])


@mcp.tool(
    name="get_bom",
    description="查询产品的物料清单（BOM），返回所有子物料",
)
async def get_bom(product_id: str) -> str:
    cli = get_client()
    data = await cli.get_bom(product_id)
    items = data if isinstance(data, list) else data.get("items", [])
    return _table(
        items,
        ["material_code", "material_name", "quantity", "scrap_rate", "is_optional", "note"],
    )


@mcp.tool(
    name="query_boms",
    description="查询 BOM 行项目，可按产品 ID 或组件物料 ID 筛选",
)
async def query_boms(product_id: str | None = None, material_id: str | None = None) -> str:
    data = await get_client().query_boms(product_id=product_id, material_id=material_id)
    return _table(data, ["id", "product_id", "material_id", "quantity", "scrap_rate", "is_optional", "note"])


@mcp.tool(
    name="get_bom_tree",
    description="递归查询产品的完整多层 BOM 树",
)
async def get_bom_tree(product_id: str) -> str:
    return _flatten(await get_client().get_bom_tree(product_id))


@mcp.tool(
    name="query_inventory",
    description="查询当前库存汇总，支持类别、关键字、低库存和分页筛选",
)
async def query_inventory(
    category: str | None = None,
    keyword: str | None = None,
    low_stock: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> str:
    data = await get_client().get_inventory(
        category=category, keyword=keyword, low_stock=low_stock,
        page=page, page_size=page_size,
    )
    items = data if isinstance(data, list) else data.get("items", [])
    return _table(items, ["material_id", "material_code", "material_name", "category", "current_stock", "safety_stock", "unit"])


@mcp.tool(
    name="check_inventory",
    description="查询库存流水记录，可按物料或交易类型筛选",
)
async def check_inventory(
    material_id: str | None = None,
    transaction_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    cli = get_client()
    data = await cli.query_inventory(
        material_id=material_id,
        transaction_type=transaction_type,
        page=page,
        page_size=page_size,
    )
    items = data if isinstance(data, list) else data.get("items", [])
    return _table(
        items,
        ["material", "transaction_type", "quantity", "before_quantity", "after_quantity", "operator", "remark"],
    )


@mcp.tool(
    name="get_material_inventory_history",
    description="获取指定物料当前库存及最近 50 条库存变动历史",
)
async def get_material_inventory_history(material_id: str) -> str:
    return _flatten(await get_client().get_material_inventory_history(material_id))


@mcp.tool(
    name="query_sales_orders",
    description="查询销售订单列表，支持按状态、日期、关键字筛选",
)
async def query_sales_orders(
    status: str | None = None,
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    cli = get_client()
    data = await cli.query_sales_orders(
        status=status, keyword=keyword,
        start_date=start_date, end_date=end_date,
        page=page, page_size=page_size,
    )
    items = data if isinstance(data, list) else data.get("items", [])
    return _table(
        items,
        ["id", "order_no", "customer_info", "order_date", "status", "total_amount", "express_no"],
    )


@mcp.tool(
    name="get_sales_order",
    description="按订单 ID 或订单号获取单个销售订单的详细信息（含明细行）",
)
async def get_sales_order(order_id: str) -> str:
    cli = get_client()
    data = await cli.get_sales_order(order_id)
    return _flatten(data)


@mcp.tool(
    name="get_sales_order_images",
    description="按订单 ID 或订单号查询销售订单的发货和物流凭证图片",
)
async def get_sales_order_images(order_id: str) -> str:
    data = await get_client().get_sales_order_images(order_id)
    return _table(data, ["id", "image_type", "image_url", "sort_order", "created_at"])


@mcp.tool(
    name="publish_sales_order",
    description="按订单 ID 或订单号发布草稿销售订单并扣减产品库存。此操作会修改订单和库存，必须显式确认",
)
async def publish_sales_order(order_id: str, confirm: bool = False) -> str:
    if not confirm:
        raise ValueError("发布会扣减库存；确认后请设置 confirm=true")
    data = await get_client().publish_sales_order(order_id)
    return _flatten(data)


@mcp.tool(
    name="query_production_orders",
    description="查询生产订单列表，支持按状态、关键字筛选",
)
async def query_production_orders(
    status: str | None = None,
    keyword: str | None = None,
    product_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    cli = get_client()
    data = await cli.query_production_orders(
        status=status, keyword=keyword, product_id=product_id,
        start_date=start_date, end_date=end_date,
        page=page, page_size=page_size,
    )
    items = data if isinstance(data, list) else data.get("items", [])
    return _table(
        items,
        ["id", "order_no", "product", "quantity", "completed_quantity", "status", "start_date", "end_date"],
    )


@mcp.tool(
    name="get_production_order",
    description="按订单 ID 或订单号获取单个生产订单的详细信息（含物料需求明细）",
)
async def get_production_order(order_id: str) -> str:
    cli = get_client()
    data = await cli.get_production_order(order_id)
    return _flatten(data)


@mcp.tool(
    name="get_production_order_images",
    description="按订单 ID 或订单号查询生产订单的产品图片",
)
async def get_production_order_images(order_id: str) -> str:
    data = await get_client().get_production_order_images(order_id)
    return _table(data, ["id", "image_type", "image_url", "sort_order", "created_at"])


@mcp.tool(
    name="get_production_materials",
    description="按订单 ID 或订单号查询生产订单的物料需求、已消耗数量和库存充足情况",
)
async def get_production_materials(order_id: str) -> str:
    return _flatten(await get_client().get_production_materials(order_id))


@mcp.tool(
    name="publish_production_order",
    description="按订单 ID 或订单号发布草稿生产订单并按 BOM 扣减原料库存。此操作会修改订单和库存，必须显式确认",
)
async def publish_production_order(order_id: str, confirm: bool = False) -> str:
    if not confirm:
        raise ValueError("发布会按 BOM 扣减原料库存；确认后请设置 confirm=true")
    data = await get_client().publish_production_order(order_id)
    return _flatten(data)


@mcp.tool(
    name="get_dashboard_stats",
    description="获取系统概览统计数据（物料数、销售订单数、生产订单数）",
)
async def get_dashboard_stats() -> str:
    cli = get_client()
    stats = await cli.get_dashboard()
    return "\n".join(f"{k}: {v}" for k, v in stats.items())


# ====================================================================
# Entry point
# ====================================================================

if __name__ == "__main__":
    print(f"[MCP] Starting ProductDB MCP Server...", file=sys.stderr)
    print(f"[MCP] API: {os.environ.get('PRODUCTDB_API_URL', 'http://localhost:8100/api/v1')}", file=sys.stderr)

    async def _auth_check() -> None:
        try:
            await get_client().validate_token()
            print("[MCP] Authentication OK", file=sys.stderr)
        except Exception as exc:
            print(f"[MCP] Authentication failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    try:
        asyncio.run(_auth_check())
    except SystemExit:
        raise
    mcp.run(transport="stdio")
