from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date
import random
import string

from app.database import get_db
from app.models import (
    ProductionOrder, ProductionOrderItem, ProductionOrderStatusEnum,
    SalesOrder, Material, BOM
)
from app.schemas import (
    ProductionOrderCreate, ProductionOrderUpdate, ProductionOrderResponse,
    ProductionOrderListResponse
)
from app.utils.auth import get_current_active_user
from app.models import User

router = APIRouter(prefix="/production-orders", tags=["生产订单"])


def generate_production_no() -> str:
    """生成生产单号"""
    today = date.today().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"PO{today}{random_str}"


@router.get("", response_model=ProductionOrderListResponse)
def get_production_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ProductionOrderStatusEnum] = None,
    product_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取生产订单列表"""
    query = db.query(ProductionOrder)
    
    if status:
        query = query.filter(ProductionOrder.status == status)
    if product_id:
        query = query.filter(ProductionOrder.product_id == product_id)
    if start_date:
        query = query.filter(ProductionOrder.start_date >= start_date)
    if end_date:
        query = query.filter(ProductionOrder.end_date <= end_date)
    
    total = query.count()
    items = query.order_by(ProductionOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {"total": total, "items": items}


@router.post("", response_model=ProductionOrderResponse, status_code=status.HTTP_201_CREATED)
def create_production_order(
    order_data: ProductionOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建生产订单"""
    # 检查产品是否存在
    product = db.query(Material).filter(Material.id == order_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    # 如果有关联销售订单，检查是否存在
    if order_data.sales_order_id:
        sales_order = db.query(SalesOrder).filter(
            SalesOrder.id == order_data.sales_order_id
        ).first()
        if not sales_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联的销售订单不存在"
            )
    
    # 生成生产单号
    order_no = generate_production_no()
    
    # 创建生产订单
    db_order = ProductionOrder(
        order_no=order_no,
        sales_order_id=order_data.sales_order_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        start_date=order_data.start_date,
        end_date=order_data.end_date,
        remark=order_data.remark,
        status=ProductionOrderStatusEnum.PENDING
    )
    db.add(db_order)
    db.flush()
    
    # 自动计算物料需求（基于BOM）
    boms = db.query(BOM).filter(BOM.product_id == order_data.product_id).all()
    
    for bom in boms:
        # 计算所需数量（含损耗）
        required_quantity = order_data.quantity * bom.quantity * (1 + bom.scrap_rate / 100)
        
        db_item = ProductionOrderItem(
            production_order_id=db_order.id,
            material_id=bom.material_id,
            quantity=required_quantity
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    
    return db_order


@router.get("/{order_id}", response_model=ProductionOrderResponse)
def get_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取生产订单详情"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )
    return order


@router.put("/{order_id}", response_model=ProductionOrderResponse)
def update_production_order(
    order_id: UUID,
    order_data: ProductionOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新生产订单"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )
    
    for key, value in order_data.dict(exclude_unset=True).items():
        setattr(order, key, value)
    
    db.commit()
    db.refresh(order)
    
    return order


@router.put("/{order_id}/status", response_model=ProductionOrderResponse)
def update_production_status(
    order_id: UUID,
    status: ProductionOrderStatusEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新生产订单状态"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )
    
    order.status = status
    
    # 如果开始生产，自动扣减库存
    if status == ProductionOrderStatusEnum.IN_PRODUCTION:
        for item in order.items:
            material = db.query(Material).filter(Material.id == item.material_id).first()
            if material.current_stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"物料 {material.name} 库存不足"
                )
            material.current_stock -= item.quantity
    
    # 如果生产完成，更新完成数量
    if status == ProductionOrderStatusEnum.COMPLETED:
        order.completed_quantity = order.quantity
    
    db.commit()
    db.refresh(order)
    
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除生产订单"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )
    
    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待生产状态的订单可以删除"
        )
    
    db.delete(order)
    db.commit()
    
    return None


@router.get("/{order_id}/materials")
def get_required_materials(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取生产订单所需的物料列表"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )
    
    result = []
    for item in order.items:
        material = db.query(Material).filter(Material.id == item.material_id).first()
        result.append({
            "material_id": str(material.id),
            "material_code": material.code,
            "material_name": material.name,
            "required_quantity": float(item.quantity),
            "consumed_quantity": float(item.consumed_quantity),
            "current_stock": float(material.current_stock),
            "is_sufficient": material.current_stock >= item.quantity
        })
    
    return result