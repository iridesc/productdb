"""ProductDB API client using an administrator-issued system token (async)."""

import os
import httpx
from uuid import UUID

API_BASE = os.environ.get("PRODUCTDB_API_URL", "http://localhost:8100/api/v1")
API_TOKEN = os.environ.get("PRODUCTDB_SYSTEM_TOKEN")


class ProductDBAPIError(RuntimeError):
    pass


class ProductDBClient:
    """Async HTTP client that forwards a system token to ProductDB."""

    def __init__(self, token: str | None = None):
        self._token = token or API_TOKEN
        if not self._token:
            raise RuntimeError("PRODUCTDB_SYSTEM_TOKEN is required (or pass a token)")
        self._http = httpx.AsyncClient(
            base_url=API_BASE,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=30.0,
        )

    async def validate_token(self) -> None:
        """Fail the MCP startup handshake unless ProductDB accepts the token."""
        response = await self._http.get("/users/me")
        self._ensure_success(response)

    @staticmethod
    def _ensure_success(response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ProductDBAPIError(f"ProductDB API {response.status_code}: {detail}")

    async def _get(self, path: str, **params):
        response = await self._http.get(path, params={k: v for k, v in params.items() if v is not None})
        self._ensure_success(response)
        return response.json()

    async def _put(self, path: str):
        response = await self._http.put(path)
        self._ensure_success(response)
        return response.json()

    async def _post(self, path: str, payload: dict):
        response = await self._http.post(path, json=payload)
        self._ensure_success(response)
        return response.json()

    # ---- materials ----

    async def query_materials(self, **params):
        return await self._get("/materials", **params)

    async def get_material(self, id_or_code: str):
        try:
            return await self._get(f"/materials/{id_or_code}")
        except ProductDBAPIError as exc:
            if "API 422" not in str(exc):
                raise
            data = await self.query_materials(keyword=id_or_code, page=1, page_size=100)
            match = next((item for item in data.get("items", []) if item.get("code") == id_or_code), None)
            if match is None:
                raise ValueError(f"Material not found: {id_or_code}") from exc
            return await self._get(f"/materials/{match['id']}")

    async def get_material_images(self, material_id: str):
        return await self._get(f"/materials/{material_id}/images")

    async def query_material_categories(self, parent_id: str | None = None):
        return await self._get("/material-categories", parent_id=parent_id)

    # ---- BOM ----

    async def get_bom(self, product_id: str):
        return await self._get(f"/boms/product/{product_id}")

    async def query_boms(self, product_id: str | None = None, material_id: str | None = None):
        return await self._get("/boms", product_id=product_id, material_id=material_id)

    async def get_bom_tree(self, product_id: str):
        return await self._get(f"/boms/tree/{product_id}")

    # ---- sales orders ----

    async def query_sales_orders(self, **params):
        return await self._get("/sales-orders", **params)

    async def create_sales_order(self, payload: dict):
        return await self._post("/sales-orders", payload)

    async def _resolve_sales_order_id(self, id_or_no: str) -> str:
        try:
            UUID(id_or_no)
            return id_or_no
        except ValueError:
            data = await self.query_sales_orders(keyword=id_or_no, page=1, page_size=100)
            match = next((item for item in data.get("items", []) if item.get("order_no") == id_or_no), None)
            if match is None:
                raise ValueError(f"Sales order not found: {id_or_no}")
            return match["id"]

    async def get_sales_order(self, order_id: str):
        return await self._get(f"/sales-orders/{await self._resolve_sales_order_id(order_id)}")

    async def publish_sales_order(self, order_id: str):
        return await self._put(f"/sales-orders/{await self._resolve_sales_order_id(order_id)}/publish")

    async def get_sales_order_images(self, order_id: str):
        return await self._get(f"/sales-orders/{await self._resolve_sales_order_id(order_id)}/images")

    # ---- production orders ----

    async def query_production_orders(self, **params):
        return await self._get("/production-orders", **params)

    async def create_production_order(self, payload: dict):
        return await self._post("/production-orders", payload)

    async def _resolve_production_order_id(self, id_or_no: str) -> str:
        try:
            UUID(id_or_no)
            return id_or_no
        except ValueError:
            data = await self.query_production_orders(keyword=id_or_no, page=1, page_size=100)
            match = next((item for item in data.get("items", []) if item.get("order_no") == id_or_no), None)
            if match is None:
                raise ValueError(f"Production order not found: {id_or_no}")
            return match["id"]

    async def get_production_order(self, order_id: str):
        return await self._get(f"/production-orders/{await self._resolve_production_order_id(order_id)}")

    async def get_production_materials(self, order_id: str):
        return await self._get(f"/production-orders/{await self._resolve_production_order_id(order_id)}/materials")

    async def publish_production_order(self, order_id: str):
        return await self._put(f"/production-orders/{await self._resolve_production_order_id(order_id)}/publish")

    async def get_production_order_images(self, order_id: str):
        return await self._get(f"/production-orders/{await self._resolve_production_order_id(order_id)}/images")

    # ---- inventory ----

    async def query_inventory(self, **params):
        return await self._get("/inventory/transactions", **params)

    async def get_inventory(self, **params):
        return await self._get("/inventory", **params)

    async def get_material_inventory_history(self, material_id: str):
        return await self._get(f"/inventory/{material_id}/history")

    # ---- dashboard ----

    async def get_dashboard(self) -> dict:
        responses = [
            await self._http.get("/materials", params={"page": 1, "page_size": 1}),
            await self._http.get("/sales-orders", params={"page": 1, "page_size": 1}),
            await self._http.get("/production-orders", params={"page": 1, "page_size": 1}),
        ]
        for response in responses:
            response.raise_for_status()
        m, s, p = (response.json() for response in responses)
        return {
            "物料总数": m.get("total", 0),
            "销售订单数": s.get("total", 0),
            "生产订单数": p.get("total", 0),
        }


# Module-level singleton
_client: ProductDBClient | None = None
_current_token: str | None = None


def get_client(token: str | None = None) -> ProductDBClient:
    """Return a cached client. Pass a token to switch credentials (e.g. per-request MCP token)."""
    global _client, _current_token
    effective = token or API_TOKEN
    if _client is None or effective != _current_token:
        _client = ProductDBClient(token=effective)
        _current_token = effective
    return _client
