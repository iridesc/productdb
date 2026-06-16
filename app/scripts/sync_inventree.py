#!/usr/bin/env python3
"""
Inventree → ProductDB 物料数据同步脚本

从 Inventree 拉取所有 Part，按 code 去重后创建或更新到 ProductDB 中。
支持幂等运行——重复执行不会产生重复记录。

用法:
  podman exec productdb-api python /app/app/scripts/sync_inventree.py \
    --inventree-token "inv-..." \
    --productdb-password "xxx"
"""

import argparse
import io
import logging
import os
import sys
import time

import requests

# ============================================================
# Configuration
# ============================================================
PAGE_SIZE = 100
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds


# ============================================================
# InvenTree Client
# ============================================================
class InvenTreeClient:
    """HTTP client for the Inventree REST API."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {token}",
            "Accept": "application/json",
        })

    def _get_paginated(self, path: str, params: dict | None = None):
        """Generator that handles Inventree's paginated API."""
        if params is None:
            params = {}
        offset = 0
        limit = PAGE_SIZE
        while True:
            params["limit"] = limit
            params["offset"] = offset
            resp = self._request_with_retry("GET", f"{self.base_url}{path}", params=params)
            data = resp.json()
            # Inventree returns {"count": N, "results": [...], "next": "..."}
            results = data.get("results", [])
            if not results:
                break
            for item in results:
                yield item
            offset += limit
            if offset >= data.get("count", offset):
                break

    def get_parts(self):
        """Yield all parts from Inventree."""
        yield from self._get_paginated("/api/part/")

    def get_boms(self):
        """Yield all BOM items from Inventree."""
        yield from self._get_paginated("/api/bom/")

    def download_image(self, image_path: str) -> tuple[bytes, str] | None:
        """Download an image from Inventree. Returns (bytes, filename) or None."""
        full_url = f"{self.base_url}{image_path}"
        resp = self._request_with_retry("GET", full_url, stream=True)
        if resp.status_code == 200 and resp.content:
            filename = os.path.basename(image_path) or "image.jpg"
            return resp.content, filename
        logging.warning(f"  Image not found or empty: {full_url}")
        return None

    def _request_with_retry(self, method: str, url: str, **kwargs):
        """HTTP request with retry logic."""
        for attempt in range(RETRY_COUNT):
            try:
                resp = self.session.request(method, url, timeout=30, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                if attempt < RETRY_COUNT - 1:
                    wait = RETRY_DELAY * (2 ** attempt)
                    logging.debug(f"  Retry {attempt + 1}/{RETRY_COUNT} in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    raise


# ============================================================
# ProductDB Client
# ============================================================
class ProductDBClient:
    """HTTP client for the ProductDB REST API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def login(self, username: str, password: str):
        """Authenticate and get JWT bearer token."""
        resp = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": username, "password": password},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        return token

    def get_materials(self) -> dict[str, dict]:
        """Fetch all existing materials. Returns {code: {id, has_images}}."""
        result = {}
        page = 1
        while True:
            resp = self._request_with_retry(
                "GET",
                f"{self.base_url}/api/v1/materials",
                params={"page": page, "page_size": PAGE_SIZE},
            )
            data = resp.json()
            for item in data.get("items", []):
                code = item.get("code")
                if code:
                    result[code] = {
                        "id": item["id"],
                        "has_images": bool(item.get("thumbnail_url")),
                    }
            total = data.get("total", 0)
            if page * PAGE_SIZE >= total:
                break
            page += 1
        return result

    def create_material(self, data: dict) -> dict | None:
        """Create a new material. Returns the created object or None on 400."""
        resp = self._request_with_retry(
            "POST",
            f"{self.base_url}/api/v1/materials",
            json=data,
        )
        if resp.status_code == 400:
            logging.warning(f"  Create failed (400): {resp.json().get('detail', resp.text)}")
            return None
        resp.raise_for_status()
        return resp.json()

    def update_material(self, material_id: str, data: dict) -> dict:
        """Update an existing material (partial)."""
        # PUT to /materials/{id} does partial update (exclude_unset)
        resp = self._request_with_retry(
            "PUT",
            f"{self.base_url}/api/v1/materials/{material_id}",
            json=data,
        )
        resp.raise_for_status()
        return resp.json()

    def upload_image(self, material_id: str, image_bytes: bytes, filename: str) -> dict | None:
        """Upload an image for a material."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            filename = filename + ".jpg"
        resp = self._request_with_retry(
            "POST",
            f"{self.base_url}/api/v1/materials/{material_id}/images",
            files={"file": (filename, io.BytesIO(image_bytes), "image/jpeg")},
        )
        if resp.status_code == 400:
            logging.warning(f"  Image upload failed (400): {resp.json().get('detail', resp.text)}")
            return None
        resp.raise_for_status()
        return resp.json()

    def create_bom(self, data: dict) -> dict | None:
        """Create a BOM entry."""
        resp = self._request_with_retry(
            "POST",
            f"{self.base_url}/api/v1/boms",
            json=data,
        )
        if resp.status_code == 400:
            # Duplicate or invalid
            detail = resp.json().get("detail", resp.text)
            if "已存在" in str(detail):
                logging.debug(f"  BOM duplicate skipped: {data.get('product_id')} -> {data.get('material_id')}")
                return None
            logging.warning(f"  BOM create failed (400): {detail}")
            return None
        resp.raise_for_status()
        return resp.json()

    def get_boms_by_product(self, product_id: str) -> list:
        """Get existing BOM items for a product."""
        resp = self._request_with_retry(
            "GET",
            f"{self.base_url}/api/v1/boms/product/{product_id}",
        )
        return resp.json() if resp.status_code == 200 else []

    def _request_with_retry(self, method: str, url: str, **kwargs):
        """HTTP request with retry logic."""
        for attempt in range(RETRY_COUNT):
            try:
                resp = self.session.request(method, url, timeout=30, **kwargs)
                return resp
            except requests.RequestException as e:
                if attempt < RETRY_COUNT - 1:
                    wait = RETRY_DELAY * (2 ** attempt)
                    logging.debug(f"  Retry {attempt + 1}/{RETRY_COUNT} in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    raise


# ============================================================
# Field Mapping
# ============================================================
def map_inventree_to_productdb(part: dict) -> dict:
    """Convert an Inventree part dict to a ProductDB material dict."""
    # Category: only "产品" → product, everything else → component
    category_name = (part.get("category_name") or "").strip()
    category = "product" if category_name == "产品" else "component"

    # Code: use IPN if present, otherwise "INV-{pk}"
    code = (part.get("IPN") or "").strip()
    if not code:
        code = f"INV-{part['pk']}"

    # Unit: use units field, default "个"
    unit = (part.get("units") or "").strip() or "个"

    pricing_min = part.get("pricing_min")
    pricing_max = part.get("pricing_max")

    return {
        "code": code,
        "name": (part.get("name") or "").strip(),
        "description": (part.get("description") or "").strip() or None,
        "category": category,
        "unit": unit,
        "safety_stock": float(part.get("minimum_stock") or 0),
        "current_stock": float(part.get("total_in_stock") or 0),
        "price": float(pricing_min) if pricing_min is not None else 0,
        "sale_price": float(pricing_max) if pricing_max is not None else 0,
        "is_active": bool(part.get("active", True)),
    }


# ============================================================
# CLI
# ============================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Sync materials from InvenTree to ProductDB"
    )
    parser.add_argument(
        "--inventree-url",
        default=os.environ.get("INVENTREE_URL", "https://productdb.irid.cc"),
        help="Inventree base URL",
    )
    parser.add_argument(
        "--inventree-token",
        default=os.environ.get("INVENTREE_TOKEN", ""),
        help="Inventree API token",
    )
    parser.add_argument(
        "--productdb-url",
        default=os.environ.get("PRODUCTDB_URL", "http://localhost:8001"),
        help="ProductDB base URL",
    )
    parser.add_argument(
        "--productdb-username",
        default=os.environ.get("PRODUCTDB_USERNAME", "admin"),
        help="ProductDB username for API auth",
    )
    parser.add_argument(
        "--productdb-password",
        default=os.environ.get("PRODUCTDB_PASSWORD", ""),
        help="ProductDB password for API auth",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        default=bool(os.environ.get("SKIP_IMAGES")),
        help="Skip image download/upload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=bool(os.environ.get("DRY_RUN")),
        help="Only show what would be done, do not make changes",
    )
    return parser.parse_args()


# ============================================================
# Main
# ============================================================
def main():
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if not args.inventree_token:
        logging.error("Inventree token is required. Use --inventree-token or INVENTREE_TOKEN env var.")
        sys.exit(1)

    if not args.productdb_password:
        logging.error("ProductDB password is required. Use --productdb-password or PRODUCTDB_PASSWORD env var.")
        sys.exit(1)

    # --- Initialize clients ---
    inventree = InvenTreeClient(args.inventree_url, args.inventree_token)
    productdb = ProductDBClient(args.productdb_url)

    # --- Authenticate to ProductDB ---
    logging.info("Authenticating to ProductDB...")
    try:
        productdb.login(args.productdb_username, args.productdb_password)
        logging.info("  Authentication successful.")
    except requests.RequestException as e:
        logging.error(f"  Auth failed: {e}")
        sys.exit(1)

    # --- Fetch Inventree parts ---
    logging.info("Fetching parts from InvenTree...")
    parts = list(inventree.get_parts())
    logging.info(f"  Found {len(parts)} parts.")

    if not parts:
        logging.warning("No parts found. Exiting.")
        return

    # --- Fetch existing ProductDB materials ---
    logging.info("Fetching existing materials from ProductDB...")
    existing = productdb.get_materials()
    logging.info(f"  Found {len(existing)} existing materials.")

    # --- Sync ---
    created = 0
    updated = 0
    skipped = 0
    images_ok = 0
    errors: list[tuple[str, str, str]] = []

    logging.info(f"{'DRY RUN: ' if args.dry_run else ''}Syncing {len(parts)} parts...")

    for i, part in enumerate(parts, 1):
        pk = part["pk"]
        data = map_inventree_to_productdb(part)
        code = data["code"]
        name = data["name"]

        try:
            if code in existing:
                # --- Update ---
                material_id = existing[code]["id"]
                has_images = existing[code]["has_images"]
                if not args.dry_run:
                    productdb.update_material(material_id, data)
                updated += 1
                action = "updated"
            else:
                # --- Create ---
                if args.dry_run:
                    material_id = "DRY-RUN"
                else:
                    resp = productdb.create_material(data)
                    if resp is None:
                        skipped += 1
                        continue
                    material_id = resp["id"]
                existing[code] = {"id": material_id, "has_images": False}
                created += 1
                has_images = False
                action = "created"

            # --- Image ---
            image_path = part.get("image")
            if image_path and not has_images and not args.skip_images:
                if not args.dry_run:
                    result = inventree.download_image(image_path)
                    if result:
                        image_bytes, filename = result
                        productdb.upload_image(material_id, image_bytes, filename)
                        existing[code]["has_images"] = True
                        images_ok += 1

            if i % 10 == 0 or i == len(parts):
                logging.info(
                    f"  [{i}/{len(parts)}] {action}: {code} | {name[:30]}"
                )

        except Exception as e:
            errors.append((code, name, str(e)))
            logging.error(f"  [{i}/{len(parts)}] ERROR: {code} ({name[:20]}...): {e}")

    # --- Sync BOM ---
    boms_created = 0
    boms_skipped = 0

    if not args.dry_run:
        # Build pk -> material_uuid lookup from the parts we just synced
        pk_to_uuid: dict[int, str] = {}
        for part in parts:
            pk = part["pk"]
            code = (part.get("IPN") or "").strip() or f"INV-{pk}"
            if code in existing:
                pk_to_uuid[pk] = existing[code]["id"]

        logging.info(f"Built PK→UUID lookup for {len(pk_to_uuid)} parts.")

        # Fetch and sync BOM items
        logging.info("Fetching BOM items from InvenTree...")
        boms = list(inventree.get_boms())
        logging.info(f"  Found {len(boms)} BOM items.")

        for bom in boms:
            part_pk = bom["part"]
            sub_part_pk = bom["sub_part"]
            product_id = pk_to_uuid.get(part_pk)
            material_id = pk_to_uuid.get(sub_part_pk)

            if not product_id or not material_id:
                boms_skipped += 1
                continue

            bom_data = {
                "product_id": product_id,
                "material_id": material_id,
                "quantity": float(bom.get("quantity") or 0),
                "scrap_rate": float(bom.get("attrition") or 0),
                "is_optional": bool(bom.get("optional", False)),
                "note": (bom.get("note") or "").strip() or None,
            }

            try:
                result = productdb.create_bom(bom_data)
                if result:
                    boms_created += 1
                else:
                    boms_skipped += 1
            except Exception as e:
                boms_skipped += 1
                logging.debug(f"  BOM error ({part_pk}->{sub_part_pk}): {e}")

        logging.info(f"  BOM created: {boms_created}, skipped: {boms_skipped}")

    # --- Summary ---
    logging.info("=" * 55)
    logging.info(f"Sync {'DRY RUN ' if args.dry_run else ''}Complete!")
    logging.info(f"  Materials created:  {created}")
    logging.info(f"  Materials updated:  {updated}")
    logging.info(f"  Materials skipped:  {skipped}")
    if not args.skip_images:
        logging.info(f"  Images uploaded:    {images_ok}")
    logging.info(f"  BOM items created:  {boms_created}")
    logging.info(f"  BOM items skipped:  {boms_skipped}")
    logging.info(f"  Errors:             {len(errors)}")
    if errors:
        for code, name, err in errors:
            logging.info(f"    - {code} ({name[:30]}): {err}")
    logging.info("=" * 55)


if __name__ == "__main__":
    main()
