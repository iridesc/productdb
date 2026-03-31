from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from database import get_db
from models import BOM, Material
from schemas import BOMCreate, BOMResponse, BOMWithProductResponse
from utils.auth import get_current_active_user
from models import User

router = APIRouter(prefix="/boms", tags=["BOM管理"])


@router.get("", response_model=List[BOMResponse])
def get_boms(
    product_id: Optional[UUID] = None,
    material_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取BOM列表"""
    query = db.query(BOM)
    
    if product_id:
        query = query.filter(BOM.product_id == product_id)
    if material_id:
        query = query.filter(BOM.material_id == material_id)
    
    return query.all()


@router.get("/product/{product_id}", response_model=List[BOMWithProductResponse])
def get_product_bom(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取产品的BOM（包含物料详情）"""
    boms = db.query(BOM).filter(BOM.product_id == product_id).all()
    
    result = []
    for bom in boms:
        result.append(BOMWithProductResponse(
            id=bom.id,
            product_id=bom.product_id,
            product_name=bom.product.name,
            product_code=bom.product.code,
            material_id=bom.material_id,
            material_name=bom.material.name,
            material_code=bom.material.code,
            quantity=bom.quantity,
            scrap_rate=bom.scrap_rate,
            is_optional=bom.is_optional,
            note=bom.note
        ))
    
    return result


@router.post("", response_model=BOMResponse, status_code=status.HTTP_201_CREATED)
def create_bom(
    bom_data: BOMCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建BOM项"""
    # 检查产品是否存在
    product = db.query(Material).filter(Material.id == bom_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    # 检查物料是否存在
    material = db.query(Material).filter(Material.id == bom_data.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物料不存在"
        )
    
    # 检查是否已存在相同的BOM
    existing = db.query(BOM).filter(
        BOM.product_id == bom_data.product_id,
        BOM.material_id == bom_data.material_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该产品的BOM中已存在此物料"
        )
    
    db_bom = BOM(**bom_data.dict())
    db.add(db_bom)
    db.commit()
    db.refresh(db_bom)
    
    return db_bom


@router.delete("/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bom(
    bom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除BOM项"""
    bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM项不存在"
        )
    
    db.delete(bom)
    db.commit()
    
    return None


@router.get("/tree/{product_id}")
def get_bom_tree(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取产品的BOM树（递归展示所有层级的物料）"""
    
    def build_tree(material_id: UUID, quantity: float) -> dict:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return None
        
        # 获取该物料的子级BOM
        children = db.query(BOM).filter(BOM.product_id == material_id).all()
        
        tree = {
            "material_id": str(material_id),
            "material_code": material.code,
            "material_name": material.name,
            "category": material.category.value,
            "quantity": quantity,
            "children": []
        }
        
        for child in children:
            # 计算实际用量（含损耗）
            actual_quantity = child.quantity * (1 + child.scrap_rate / 100)
            child_tree = build_tree(child.material_id, actual_quantity)
            if child_tree:
                tree["children"].append(child_tree)
        
        return tree
    
    return build_tree(product_id, 1.0)