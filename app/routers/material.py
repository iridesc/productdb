from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.models import Material, MaterialCategory, MaterialImage, User, BOM
from app.models.transaction import SalesOrder, SalesOrderItem, ProductionOrder, ProductionOrderItem, InventoryTransaction
from app.schemas import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MaterialListResponse,
    MaterialCategoryCreate,
    MaterialCategoryResponse,
)
from app.utils.auth import get_current_active_user, get_password_hash

router = APIRouter(prefix="/materials", tags=["物料管理"])


def calculate_bom_cost(material: Material, db: Session) -> Decimal:
    """计算物料的BOM成本"""
    boms = db.query(BOM).filter(BOM.product_id == material.id).all()
    total_cost = Decimal("0")
    for bom in boms:
        component = db.query(Material).filter(Material.id == bom.material_id).first()
        if component:
            component_cost = component.price * bom.quantity
            total_cost += component_cost
    return total_cost


def add_cost_to_material(material: Material, db: Session) -> dict:
    """为物料添加计算的成本字段"""
    bom_cost = calculate_bom_cost(material, db)
    total_cost = bom_cost + (material.other_cost or Decimal("0"))

    material_dict = {
        "id": material.id,
        "code": material.code,
        "name": material.name,
        "category": material.category,
        "unit": material.unit,
        "specification": material.specification,
        "safety_stock": material.safety_stock,
        "current_stock": material.current_stock,
        "price": material.price,
        "sale_price": material.sale_price,
        "other_cost": material.other_cost,
        "description": material.description,
        "is_active": material.is_active,
        "category_id": material.category_id,
        "created_at": material.created_at,
        "updated_at": material.updated_at,
        "category_info": material.category_info,
        "bom_cost": bom_cost,
        "total_cost": total_cost,
        "thumbnail_url": material.thumbnail_url,
    }
    return material_dict


@router.get("", response_model=MaterialListResponse)
def get_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_by: Optional[str] = Query(None, description="排序字段"),
    sort_order: Optional[str] = Query("asc", description="排序方向 asc/desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取物料列表"""
    query = db.query(Material).options(selectinload(Material.images))

    if category:
        categories = [c.strip() for c in category.split(',') if c.strip()]
        if categories:
            query = query.filter(Material.category.in_(categories))
    if keyword:
        query = query.filter(
            (Material.name.contains(keyword)) | (Material.code.contains(keyword))
        )
    if is_active is not None:
        query = query.filter(Material.is_active == is_active)

    # 排序
    sortable_columns = {
        'code': Material.code,
        'name': Material.name,
        'category': Material.category,
        'current_stock': Material.current_stock,
        'safety_stock': Material.safety_stock,
        'unit': Material.unit,
    }
    if sort_by and sort_by in sortable_columns:
        col = sortable_columns[sort_by]
        query = query.order_by(col.desc()) if sort_order == 'desc' else query.order_by(col)
    else:
        query = query.order_by(Material.code)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    items_with_cost = [add_cost_to_material(item, db) for item in items]

    return {"total": total, "items": items_with_cost}


@router.post("", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material_data: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建物料"""
    # 检查编码是否存在
    existing = db.query(Material).filter(Material.code == material_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="物料编码已存在"
        )

    db_material = Material(**material_data.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)

    return add_cost_to_material(db_material, db)


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取物料详情"""
    material = db.query(Material).options(selectinload(Material.images)).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物料不存在")
    return add_cost_to_material(material, db)


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: UUID,
    material_data: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新物料"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物料不存在")

    for key, value in material_data.dict(exclude_unset=True).items():
        setattr(material, key, value)

    db.commit()
    db.refresh(material)

    return add_cost_to_material(material, db)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: UUID,
    cascade: bool = Query(False, description="是否级联删除所有关联数据（销售订单、生产订单、库存记录）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除物料"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物料不存在")

    # ===== 收集所有外键依赖 =====
    dependencies = {}

    # 1. BOM 依赖（此物料作为组件被其他产品引用）
    dependent_boms = db.query(BOM).filter(BOM.material_id == material_id).all()
    if dependent_boms:
        product_names = []
        for bom in dependent_boms:
            product = db.query(Material).filter(Material.id == bom.product_id).first()
            if product:
                product_names.append(f"{product.code} - {product.name}")
        dependencies["bom"] = {
            "message": f"此物料被 {len(dependent_boms)} 个产品的BOM引用为组件",
            "products": product_names,
        }

    # 2. 销售订单依赖（此物料被作为商品）
    so_items = db.query(SalesOrderItem).filter(SalesOrderItem.product_id == material_id).all()
    if so_items:
        order_ids = list(set(i.order_id for i in so_items))
        orders = db.query(SalesOrder).filter(SalesOrder.id.in_(order_ids)).all()
        dependencies["sales_orders"] = {
            "message": f"此物料被 {len(so_items)} 个销售订单行项目引用，涉及 {len(orders)} 个销售订单",
            "orders": [{"id": str(o.id), "order_no": o.order_no} for o in orders],
        }

    # 3. 生产订单依赖（此物料作为生产成品）
    po_as_product = db.query(ProductionOrder).filter(ProductionOrder.product_id == material_id).all()
    if po_as_product:
        dependencies["production_orders"] = {
            "message": f"此物料被 {len(po_as_product)} 个生产订单引用为生产成品",
            "orders": [{"id": str(o.id), "order_no": o.order_no} for o in po_as_product],
        }

    # 4. 生产订单物料依赖（此物料作为生产原料）
    poi_items = db.query(ProductionOrderItem).filter(ProductionOrderItem.material_id == material_id).all()
    if poi_items:
        po_ids = list(set(i.production_order_id for i in poi_items))
        pos = db.query(ProductionOrder).filter(ProductionOrder.id.in_(po_ids)).all()
        dependencies["production_order_items"] = {
            "message": f"此物料被 {len(poi_items)} 个生产订单行项目引用为原料，涉及 {len(pos)} 个生产订单",
            "orders": [{"id": str(o.id), "order_no": o.order_no} for o in pos],
        }

    # 5. 库存流水依赖
    inv_count = db.query(InventoryTransaction).filter(InventoryTransaction.material_id == material_id).count()
    if inv_count > 0:
        dependencies["inventory"] = {
            "message": f"此物料有 {inv_count} 条库存流水记录",
        }

    # ===== 如果没有依赖，直接删除 =====
    if not dependencies:
        db.query(BOM).filter(BOM.product_id == material_id).delete(synchronize_session=False)
        db.delete(material)
        db.commit()
        return None

    # ===== 有依赖但未要求级联 → 返回 409 =====
    if not cascade:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "该物料存在以下依赖关系，无法直接删除",
                "dependencies": dependencies,
            },
        )

    # ===== 级联删除所有依赖 =====
    # BOM：不可级联删除（需要用户手动处理BOM结构）
    if "bom" in dependencies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法级联删除：{dependencies['bom']['message']}。请先手动修改BOM结构。",
        )

    # 销售订单项 + 订单
    if "sales_orders" in dependencies:
        order_ids = [o["id"] for o in dependencies["sales_orders"]["orders"]]
        db.query(SalesOrderItem).filter(SalesOrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
        db.query(SalesOrder).filter(SalesOrder.id.in_(order_ids)).delete(synchronize_session=False)

    # 生产订单项 + 生产订单（作为产品）
    if "production_orders" in dependencies:
        po_ids = [o["id"] for o in dependencies["production_orders"]["orders"]]
        db.query(ProductionOrderItem).filter(ProductionOrderItem.production_order_id.in_(po_ids)).delete(synchronize_session=False)
        db.query(ProductionOrder).filter(ProductionOrder.id.in_(po_ids)).delete(synchronize_session=False)

    # 生产订单项（作为原料）
    if "production_order_items" in dependencies:
        db.query(ProductionOrderItem).filter(ProductionOrderItem.material_id == material_id).delete(synchronize_session=False)

    # 库存流水
    if "inventory" in dependencies:
        db.query(InventoryTransaction).filter(InventoryTransaction.material_id == material_id).delete(synchronize_session=False)

    # 删除此物料作为产品的BOM
    db.query(BOM).filter(BOM.product_id == material_id).delete(synchronize_session=False)

    # 最后删除物料
    db.delete(material)
    db.commit()

    return None


# ==================== 物料分类 ====================

category_router = APIRouter(prefix="/material-categories", tags=["物料分类"])


@category_router.get("", response_model=List[MaterialCategoryResponse])
def get_categories(
    parent_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取物料分类列表"""
    query = db.query(MaterialCategory)
    if parent_id is None:
        query = query.filter(MaterialCategory.parent_id == None)
    else:
        query = query.filter(MaterialCategory.parent_id == parent_id)

    return query.all()


@category_router.post(
    "", response_model=MaterialCategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_category(
    category_data: MaterialCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建物料分类"""
    existing = (
        db.query(MaterialCategory)
        .filter(MaterialCategory.code == category_data.code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="分类编码已存在"
        )

    db_category = MaterialCategory(**category_data.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category
