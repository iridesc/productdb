from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.models import Material, MaterialCategory, MaterialImage, User, BOM
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
    }
    return material_dict


@router.get("", response_model=MaterialListResponse)
def get_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取物料列表"""
    query = db.query(Material).options(selectinload(Material.images))

    if category:
        query = query.filter(Material.category == category)
    if keyword:
        query = query.filter(
            (Material.name.contains(keyword)) | (Material.code.contains(keyword))
        )
    if is_active is not None:
        query = query.filter(Material.is_active == is_active)

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
    material = db.query(Material).filter(Material.id == material_id).first()
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除物料"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物料不存在")

    dependent_boms = db.query(BOM).filter(BOM.material_id == material_id).all()
    if dependent_boms:
        product_names = []
        for bom in dependent_boms:
            product = db.query(Material).filter(Material.id == bom.product_id).first()
            if product:
                product_names.append(f"{product.code} - {product.name}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除：以下物料的BOM依赖此物料：{', '.join(product_names)}。请先删除或修改这些物料的BOM。",
        )

    db.query(BOM).filter(BOM.product_id == material_id).delete()

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
