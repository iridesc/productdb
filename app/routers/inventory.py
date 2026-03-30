from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models import Material, InventoryTransaction, InventoryTransactionTypeEnum, MaterialCategoryEnum
from app.schemas import (
    InventoryTransactionCreate, InventoryTransactionResponse,
    InventoryResponse, InventoryListResponse
)
from app.utils.auth import get_current_active_user
from app.models import User

router = APIRouter(prefix="/inventory", tags=["库存管理"])


@router.get("", response_model=InventoryListResponse)
def get_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[MaterialCategoryEnum] = None,
    keyword: Optional[str] = None,
    low_stock: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取库存列表"""
    query = db.query(Material).filter(Material.is_active == True)
    
    if category:
        query = query.filter(Material.category == category)
    if keyword:
        query = query.filter(
            (Material.name.contains(keyword)) | (Material.code.contains(keyword))
        )
    if low_stock:
        query = query.filter(Material.current_stock < Material.safety_stock)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for material in items:
        result.append(InventoryResponse(
            material_id=material.id,
            material_code=material.code,
            material_name=material.name,
            category=material.category,
            unit=material.unit,
            current_stock=material.current_stock,
            safety_stock=material.safety_stock
        ))
    
    return {"total": total, "items": result}


@router.get("/transactions", response_model=List[InventoryTransactionResponse])
def get_transactions(
    material_id: Optional[UUID] = None,
    transaction_type: Optional[InventoryTransactionTypeEnum] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取库存流水记录"""
    query = db.query(InventoryTransaction)
    
    if material_id:
        query = query.filter(InventoryTransaction.material_id == material_id)
    if transaction_type:
        query = query.filter(InventoryTransaction.transaction_type == transaction_type)
    # 日期过滤暂略
    
    return query.order_by(InventoryTransaction.created_at.desc()).limit(page_size).all()


@router.post("/transactions", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: InventoryTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建库存流水（手动调整库存）"""
    # 检查物料是否存在
    material = db.query(Material).filter(Material.id == transaction_data.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物料不存在"
        )
    
    before_quantity = material.current_stock
    
    # 根据类型计算库存变化
    if transaction_data.transaction_type in [
        InventoryTransactionTypeEnum.PURCHASE,
        InventoryTransactionTypeEnum.PRODUCTION_IN
    ]:
        # 入库
        after_quantity = before_quantity + transaction_data.quantity
    elif transaction_data.transaction_type in [
        InventoryTransactionTypeEnum.PRODUCTION_OUT,
        InventoryTransactionTypeEnum.SALES_OUT
    ]:
        # 出库
        after_quantity = before_quantity - transaction_data.quantity
        if after_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="库存不足"
            )
    else:
        # 调整/转账
        after_quantity = before_quantity + transaction_data.quantity
    
    # 更新库存
    material.current_stock = after_quantity
    
    # 创建流水记录
    db_transaction = InventoryTransaction(
        material_id=transaction_data.material_id,
        transaction_type=transaction_data.transaction_type,
        quantity=transaction_data.quantity,
        before_quantity=before_quantity,
        after_quantity=after_quantity,
        reference_type=transaction_data.reference_type,
        reference_id=transaction_data.reference_id,
        operator=transaction_data.operator or current_user.username,
        remark=transaction_data.remark
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction


@router.get("/{material_id}/history")
def get_material_history(
    material_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取物料的库存历史"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物料不存在"
        )
    
    transactions = db.query(InventoryTransaction).filter(
        InventoryTransaction.material_id == material_id
    ).order_by(InventoryTransaction.created_at.desc()).limit(50).all()
    
    result = []
    for t in transactions:
        result.append({
            "id": str(t.id),
            "transaction_type": t.transaction_type.value,
            "quantity": float(t.quantity),
            "before_quantity": float(t.before_quantity),
            "after_quantity": float(t.after_quantity),
            "operator": t.operator,
            "remark": t.remark,
            "created_at": t.created_at.isoformat()
        })
    
    return {
        "material": {
            "id": str(material.id),
            "code": material.code,
            "name": material.name,
            "current_stock": float(material.current_stock),
            "safety_stock": float(material.safety_stock)
        },
        "transactions": result
    }