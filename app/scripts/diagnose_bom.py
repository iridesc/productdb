#!/usr/bin/env python3
"""
诊断脚本：检查物料在新系统中的 BOM 状态，以及在 InvenTree 中的 BOM 数据。

用法:
  # 检查单个物料
  python3 app/scripts/diagnose_bom.py \
    --inventree-url https://ollama.irid.cc \
    --inventree-token inv-... \
    --productdb-url https://productdb.irid.cc \
    --productdb-password xxx \
    --material-code 0010

  # 批量检查多个物料
  python3 app/scripts/diagnose_bom.py ... --material-code 0010 0006 part-0001

  # 检查 ProductDB 中所有缺少 BOM 的「产品」分类物料
  python3 app/scripts/diagnose_bom.py ... --all-missing
"""

import argparse
import logging
import os
import sys
from collections.abc import Callable

import requests


# ============================================================
# Clients
# ============================================================

class InventreeDiagnostic:
    """Lightweight InvenTree API client for diagnostics."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {token}",
            "Accept": "application/json",
        })

    def get_all_parts(self, on_page: Callable[[list[dict]], None] | None = None) -> list[dict]:
        """Fetch all parts from InvenTree (paginated)."""
        all_parts = []
        offset = 0
        limit = 100
        while True:
            resp = self.session.get(
                f"{self.base_url}/api/part/",
                params={"limit": limit, "offset": offset},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("results", [])
            if on_page:
                on_page(items)
            all_parts.extend(items)
            offset += limit
            if offset >= data.get("count", offset):
                break
        return all_parts

    def build_ipn_to_part(self) -> dict[str, dict]:
        """Fetch all parts and build IPN → part lookup."""
        ipn_to_part: dict[str, dict] = {}
        parts = self.get_all_parts()
        for p in parts:
            ipn = (p.get("IPN") or "").strip()
            if ipn:
                ipn_to_part[ipn] = p
        logging.info(f"  Built IPN→Part lookup from {len(parts)} Inventree parts ({len(ipn_to_part)} with IPN)")
        return ipn_to_part

    def get_part_by_pk(self, part_pk: int) -> dict | None:
        """Get a part by its PK."""
        try:
            resp = self.session.get(f"{self.base_url}/api/part/{part_pk}/", timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_part_bom(self, part_pk: int) -> list[dict]:
        """Get BOM items for a specific part by its PK."""
        all_items = []
        offset = 0
        limit = 100
        while True:
            try:
                resp = self.session.get(
                    f"{self.base_url}/api/bom/",
                    params={"part": part_pk, "limit": limit, "offset": offset},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get("results", [])
                all_items.extend(items)
                offset += limit
                if offset >= data.get("count", offset):
                    break
            except Exception as e:
                logging.warning(f"  Inventree BOM API error for part_pk={part_pk}: {e}")
                break
        return all_items

    def get_part_name(self, part_pk: int) -> str:
        """Get part name by PK."""
        try:
            resp = self.session.get(f"{self.base_url}/api/part/{part_pk}/", timeout=30)
            resp.raise_for_status()
            return resp.json().get("name", f"pk={part_pk}")
        except Exception:
            return f"pk={part_pk}"


class ProductDBDiagnostic:
    """Lightweight ProductDB API client for diagnostics."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def login(self, username: str, password: str):
        resp = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": username, "password": password},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_material_by_code(self, code: str) -> dict | None:
        resp = self.session.get(
            f"{self.base_url}/api/v1/materials",
            params={"keyword": code, "page_size": 50},
            timeout=30,
        )
        resp.raise_for_status()
        for item in resp.json().get("items", []):
            if item.get("code") == code:
                return item
        return None

    def get_all_products(self, on_page: Callable[[list[dict]], None] | None = None) -> list[dict]:
        """Fetch all materials of category='product'."""
        all_items = []
        page = 1
        while True:
            resp = self.session.get(
                f"{self.base_url}/api/v1/materials",
                params={"category": "product", "page": page, "page_size": 100},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if on_page:
                on_page(items)
            all_items.extend(items)
            if page * 100 >= data.get("total", 0):
                break
            page += 1
        return all_items

    def get_bom_by_product(self, product_id: str) -> list[dict]:
        resp = self.session.get(
            f"{self.base_url}/api/v1/boms/product/{product_id}",
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
        return []


# ============================================================
# Core
# ============================================================

def diagnose_one(args, pdb: ProductDBDiagnostic, inv: InventreeDiagnostic,
                 code: str, ipn_to_part: dict[str, dict]) -> int:
    """Diagnose a single material code. Returns: 0=OK, 1=no BOM in InvenTree, 2=missing in ProductDB, 3=BOM mismatch."""
    logging.info(f"--- Material: {code} ---")

    # ProductDB lookup
    material = pdb.get_material_by_code(code)
    if not material:
        logging.warning(f"  ❌ NOT FOUND in ProductDB")
        return 2

    product_id = material["id"]
    logging.info(f"  ProductDB: id={product_id[:8]}..., name='{material['name']}', category={material['category']}")

    pdb_boms = pdb.get_bom_by_product(product_id)
    pdb_count = len(pdb_boms)
    if pdb_boms:
        logging.info(f"  ProductDB BOM: {pdb_count} items")
        for b in pdb_boms[:5]:
            logging.info(f"    - {b.get('material_code')} | {b.get('material_name')} x{b.get('quantity')}")
        if pdb_count > 5:
            logging.info(f"    ... and {pdb_count - 5} more")

    # InvenTree lookup via IPN→part mapping
    part = ipn_to_part.get(code)
    if not part:
        # Some codes are auto-assigned (part-NNNN), not from IPN
        if code.startswith("part-"):
            logging.info(f"  InvenTree: auto-assigned code '{code}' (no IPN), cannot match to Inventree part")
        else:
            logging.info(f"  InvenTree: part with IPN='{code}' not found")
        if pdb_boms:
            logging.info(f"  ✓ BOM exists in ProductDB (probably synced via parent)")
            return 0
        else:
            logging.info(f"  ⚠️  Material has no BOM and InvenTree part not found by code")
            return 2

    part_pk = part["pk"]
    logging.info(f"  InvenTree: pk={part_pk}, name='{part['name']}', active={part.get('active')}")

    inv_boms = inv.get_part_bom(part_pk)
    inv_count = len(inv_boms)

    if inv_boms:
        logging.info(f"  InvenTree BOM: {inv_count} items")
        for b in inv_boms[:5]:
            sub_pk = b.get("sub_part")
            sub_name = inv.get_part_name(sub_pk)
            logging.info(f"    - sub_part_pk={sub_pk} ({sub_name}) x{b.get('quantity', 0)}")
        if inv_count > 5:
            logging.info(f"    ... and {inv_count - 5} more")
    else:
        logging.info(f"  InvenTree BOM: 0 items")

    # Cross-check
    if not pdb_boms and inv_boms:
        logging.warning(f"  ⚠️  MISSING BOM: InvenTree has {inv_count} items but ProductDB has 0!")
        return 3
    elif pdb_boms and inv_boms:
        status = "✓" if pdb_count == inv_count else "⚠"
        logging.info(f"  {status} BOM counts: ProductDB={pdb_count}, InvenTree={inv_count}")
        return 0 if pdb_count == inv_count else 3
    elif not pdb_boms and not inv_boms:
        logging.info(f"  ✓ Both sides have no BOM (likely empty product)")
        return 0
    else:
        # pdb_boms but no inv_boms — extra BOM in ProductDB
        logging.info(f"  ⚠️  ProductDB has {pdb_count} BOM items but InvenTree has 0")
        return 3


# ============================================================
# CLI
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="诊断 InvenTree → ProductDB BOM 同步问题（支持批量）",
        epilog="Examples:\n"
               "  # 单个物料\n"
               "  %(prog)s --material-code 0010 ...\n"
               "  # 批量\n"
               "  %(prog)s --material-code 0010 0006 part-0001 ...\n"
               "  # 检查所有缺少 BOM 的「产品」\n"
               "  %(prog)s --all-missing ...",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--inventree-url", default=os.environ.get("INVENTREE_URL", ""))
    parser.add_argument("--inventree-token", default=os.environ.get("INVENTREE_TOKEN", ""))
    parser.add_argument("--productdb-url", default=os.environ.get("PRODUCTDB_URL", ""))
    parser.add_argument("--productdb-username", default="admin")
    parser.add_argument("--productdb-password", default=os.environ.get("PRODUCTDB_PASSWORD", ""))
    parser.add_argument(
        "--material-code", nargs="+", default=[],
        help="物料编码（可传多个，空格分隔），例如: --material-code 0010 0006",
    )
    parser.add_argument(
        "--all-missing", action="store_true",
        help="检查 ProductDB 中所有「产品」分类下缺少 BOM 的物料",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if not args.material_code and not args.all_missing:
        logging.error("必须指定 --material-code 或 --all-missing")
        sys.exit(1)

    # Validate required parameters
    for name, val in [("inventree-url", args.inventree_url),
                      ("inventree-token", args.inventree_token),
                      ("productdb-url", args.productdb_url),
                      ("productdb-password", args.productdb_password)]:
        if not val:
            logging.error(f"--{name} is required (or set env var {name.upper().replace('-', '_')})")
            sys.exit(1)

    # Init clients
    pdb = ProductDBDiagnostic(args.productdb_url)
    pdb.login(args.productdb_username, args.productdb_password)
    inv = InventreeDiagnostic(args.inventree_url, args.inventree_token)

    # Pre-fetch all Inventree parts → IPN mapping (one API call, reused for all checks)
    logging.info("Building Inventree IPN→Part mapping (one-time)...")
    ipn_to_part = inv.build_ipn_to_part()
    logging.info("")

    # Gather material codes to check
    codes: list[str] = list(args.material_code)

    if args.all_missing:
        logging.info("Fetching all 'product' category materials from ProductDB...")
        products_without_bom: list[str] = []

        def check_page(items: list[dict]):
            for m in items:
                boms = pdb.get_bom_by_product(m["id"])
                if not boms:
                    products_without_bom.append(m["code"])
                    logging.info(f"  Missing BOM: {m['code']} | {m['name']}")

        products = pdb.get_all_products(on_page=check_page)
        logging.info(f"Total products: {len(products)}, missing BOM: {len(products_without_bom)}")

        codes.extend(products_without_bom)

    if not codes:
        logging.info("No materials to check.")
        return

    logging.info(f"\nChecking {len(codes)} material(s)...\n")

    # Run diagnosis
    stats = {"ok": 0, "missing_in_pdb": 0, "no_bom_in_inv": 0, "mismatch": 0}

    for i, code in enumerate(codes, 1):
        logging.info(f"[{i}/{len(codes)}]")
        result = diagnose_one(args, pdb, inv, code, ipn_to_part)
        if result == 0:
            stats["ok"] += 1
        elif result == 2:
            stats["missing_in_pdb"] += 1
        elif result == 3:
            stats["mismatch"] += 1
        else:
            stats["no_bom_in_inv"] += 1
        print()  # blank line between items

    # Summary
    logging.info("=" * 55)
    logging.info(f"Diagnosis complete for {len(codes)} material(s):")
    logging.info(f"  ✓ OK:                {stats['ok']}")
    logging.info(f"  ⚠ BOM mismatch:      {stats['mismatch']}")
    logging.info(f"  ❌ Not in ProductDB:  {stats['missing_in_pdb']}")
    logging.info(f"  ❌ No BOM in InvenTree:{stats['no_bom_in_inv']}")
    logging.info("=" * 55)


if __name__ == "__main__":
    main()
