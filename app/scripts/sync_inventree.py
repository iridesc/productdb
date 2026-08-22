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
        """Yield all BOM items from Inventree (flat endpoint — may miss some items)."""
        yield from self._get_paginated("/api/bom/")

    def get_boms_for_part(self, part_pk: int) -> list[dict]:
        """Get BOM items for a specific part (reliable per-part endpoint)."""
        return list(self._get_paginated("/api/bom/", params={"part": part_pk}))

    def get_boms_per_part(self, part_pks: list[int], progress_every: int = 20) -> list[dict]:
        """Fetch BOM items by iterating through each part. Reliable but slower."""
        all_boms = []
        total = len(part_pks)
        start = time.time()
        for i, pk in enumerate(part_pks, 1):
            items = self.get_boms_for_part(pk)
            all_boms.extend(items)
            if i % progress_every == 0 or i == total:
                elapsed = time.time() - start
                logging.info(f"  BOM fetch [{i}/{total}] {i * 100 // total}% | "
                             f"found {len(all_boms)} items so far | elapsed: {elapsed:.0f}s")
        return all_boms

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

    def create_bom(self, data: dict) -> tuple[dict | None, str]:
        """Create a BOM entry. Returns (result, status) where status is 'created', 'duplicate', or 'error'."""
        resp = self._request_with_retry(
            "POST",
            f"{self.base_url}/api/v1/boms",
            json=data,
        )
        if resp.status_code == 201:
            return resp.json(), "created"

        # Not 201 — try to understand what happened
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text

        if resp.status_code == 400:
            detail_str = detail.get("detail", str(detail)) if isinstance(detail, dict) else str(detail)
            if "已存在" in detail_str:
                logging.info(f"  BOM duplicate: prod={str(data.get('product_id'))[:8]}... → mat={str(data.get('material_id'))[:8]}...")
                return None, "duplicate"
            logging.warning(f"  BOM create failed (400): {detail_str}")
            return None, "error"

        # Other unexpected status (422, 500, etc.)
        logging.warning(f"  BOM create unexpected HTTP {resp.status_code}: {detail}")
        resp.raise_for_status()

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

    # Code: use IPN if present, empty means auto-assign later as part-0001, part-0002, ...
    code = (part.get("IPN") or "").strip()

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
        default=os.environ.get("INVENTREE_URL", ""),
        help="Inventree base URL",
    )
    parser.add_argument(
        "--inventree-token",
        default=os.environ.get("INVENTREE_TOKEN", ""),
        help="Inventree API token",
    )
    parser.add_argument(
        "--productdb-url",
        default=os.environ.get("PRODUCTDB_URL", ""),
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
    parser.add_argument(
        "--bom-only",
        action="store_true",
        default=bool(os.environ.get("BOM_ONLY")),
        help="Only sync BOM items (skip material sync)",
    )
    parser.add_argument(
        "--material-code", nargs="+", default=[],
        help="只处理指定编码的物料（可用于 BOM 过滤），例如: --material-code 0010 0008",
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

    if not args.inventree_url:
        logging.error("Inventree URL is required. Use --inventree-url or INVENTREE_URL env var.")
        sys.exit(1)

    if not args.inventree_token:
        logging.error("Inventree token is required. Use --inventree-token or INVENTREE_TOKEN env var.")
        sys.exit(1)

    if not args.productdb_url:
        logging.error("ProductDB URL is required. Use --productdb-url or PRODUCTDB_URL env var.")
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
    parts = sorted(inventree.get_parts(), key=lambda p: p["pk"])
    logging.info(f"  Found {len(parts)} parts.")

    if not parts:
        logging.warning("No parts found. Exiting.")
        return

    # --- Fetch existing ProductDB materials ---
    logging.info("Fetching existing materials from ProductDB...")
    existing = productdb.get_materials()
    logging.info(f"  Found {len(existing)} existing materials.")

    # --- Build PK→Code mapping (always needed for BOM lookup) ---
    no_code_counter = 0
    pk_to_code: dict[int, str] = {}  # Inventree PK → assigned code

    for part in parts:
        pk = part["pk"]
        data = map_inventree_to_productdb(part)
        code = data["code"]
        if not code:
            no_code_counter += 1
            code = f"part-{no_code_counter:04d}"
        pk_to_code[pk] = code

    # --- Sync materials (skip in --bom-only mode) ---
    created = 0
    updated = 0
    skipped = 0
    images_ok = 0
    errors: list[tuple[str, str, str]] = []

    if args.bom_only:
        logging.info("BOM-ONLY mode: skipping material sync.")
    else:
        logging.info(f"{'DRY RUN: ' if args.dry_run else ''}Syncing {len(parts)} parts...")

        for i, part in enumerate(parts, 1):
            pk = part["pk"]
            data = map_inventree_to_productdb(part)
            code = pk_to_code[pk]
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
    boms_duplicate = 0

    if not args.dry_run:
        # Build pk -> material_uuid lookup using codes assigned during sync
        pk_to_uuid: dict[int, str] = {}
        for part in parts:
            pk = part["pk"]
            code = pk_to_code.get(pk)
            if code and code in existing:
                pk_to_uuid[pk] = existing[code]["id"]

        logging.info(f"Built PK→UUID lookup for {len(pk_to_uuid)} parts.")

        # --- Fetch BOMs: use per-part endpoint (reliable) ---
        filter_codes = set(args.material_code)

        if filter_codes:
            # Targeted sync: only fetch BOMs for matching part PKs
            target_pks = [pk for pk, code in pk_to_code.items() if code in filter_codes]
            not_found = filter_codes - set(pk_to_code.values())
            if not_found:
                logging.warning(f"  Codes not found in Inventree parts: {not_found}")
            if not target_pks:
                logging.error("  No matching parts found for the given material codes.")
                return
            logging.info(f"Fetching BOMs for {len(target_pks)} matching part(s) (codes: {filter_codes})...")
            boms = inventree.get_boms_per_part(target_pks)
        else:
            # Full sync: iterate all parts to avoid missing any BOMs
            logging.info("Fetching BOMs per part from InvenTree (this may take a while)...")
            all_pks = [p["pk"] for p in parts]
            boms = inventree.get_boms_per_part(all_pks)

        logging.info(f"  Found {len(boms)} BOM items.")

        # Track skipped reasons for diagnosis
        skipped_parent_missing: list[tuple[int, int, str]] = []  # (part_pk, sub_part_pk, reason)
        skipped_component_missing: list[tuple[int, int, str]] = []

        bom_total = len(boms)
        bom_start_time = time.time()

        for i, bom in enumerate(boms, 1):
            part_pk = bom["part"]
            sub_part_pk = bom["sub_part"]

            product_id = pk_to_uuid.get(part_pk)
            material_id = pk_to_uuid.get(sub_part_pk)

            if not product_id and not material_id:
                boms_skipped += 1
                skipped_parent_missing.append((part_pk, sub_part_pk, "parent and component not found"))
                continue
            if not product_id:
                boms_skipped += 1
                skipped_parent_missing.append((part_pk, sub_part_pk, "parent not in ProductDB"))
                continue
            if not material_id:
                boms_skipped += 1
                skipped_component_missing.append((part_pk, sub_part_pk, "component not in ProductDB"))
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
                result, status = productdb.create_bom(bom_data)
                if status == "created":
                    boms_created += 1
                elif status == "duplicate":
                    boms_duplicate += 1
                else:
                    boms_skipped += 1
            except Exception as e:
                boms_skipped += 1
                logging.warning(f"  BOM error (part_pk={part_pk}→sub_part={sub_part_pk}): {e}")

            # Progress every 50 items or at the end
            if i % 50 == 0 or i == bom_total:
                elapsed = time.time() - bom_start_time
                pct = i * 100 // bom_total
                logging.info(
                    f"  BOM [{i}/{bom_total}] {pct}% | "
                    f"created: {boms_created} dup: {boms_duplicate} skipped: {boms_skipped} | "
                    f"elapsed: {elapsed:.0f}s"
                )

        if boms_skipped > 0:
            logging.info(f"  --- Skipped BOM details ---")
            if skipped_parent_missing:
                logging.info(f"  Parent part not found ({len(skipped_parent_missing)} items):")
                for ppk, spk, reason in skipped_parent_missing[:10]:
                    logging.info(f"    part_pk={ppk} → sub_part_pk={spk} ({reason})")
                if len(skipped_parent_missing) > 10:
                    logging.info(f"    ... and {len(skipped_parent_missing) - 10} more")
            if skipped_component_missing:
                logging.info(f"  Component sub_part not found ({len(skipped_component_missing)} items):")
                for ppk, spk, reason in skipped_component_missing[:10]:
                    # Try to find part code for context
                    part_code = pk_to_code.get(ppk, str(ppk))
                    logging.info(f"    product: pk={ppk}({part_code}) → sub_part_pk={spk} not in ProductDB")
                if len(skipped_component_missing) > 10:
                    logging.info(f"    ... and {len(skipped_component_missing) - 10} more")

    # --- Summary ---
    logging.info("=" * 55)
    mode_label = "BOM-ONLY " if args.bom_only else ("DRY RUN " if args.dry_run else "")
    logging.info(f"Sync {mode_label}Complete!")
    if not args.bom_only:
        logging.info(f"  Materials created:  {created}")
        logging.info(f"  Materials updated:  {updated}")
        logging.info(f"  Materials skipped:  {skipped}")
        if not args.skip_images:
            logging.info(f"  Images uploaded:    {images_ok}")
    logging.info(f"  BOM items created:  {boms_created}")
    logging.info(f"  BOM items duplicate:{boms_duplicate}")
    logging.info(f"  BOM items skipped:  {boms_skipped}")
    logging.info(f"  Errors:             {len(errors)}")
    if errors:
        for code, name, err in errors:
            logging.info(f"    - {code} ({name[:30]}): {err}")
    logging.info("=" * 55)


if __name__ == "__main__":
    main()
