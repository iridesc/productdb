from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date
import random
import string

from app.database import get_db
from app.models import SalesOrder, SalesOrderItem, SalesOrderStatusEnum, Customer, Material
from app.schemas import (
    SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse, SalesOrderListResponse,
    SalesOrderItemCreate, SalesOrderItemResponse
)
from app.utils.auth import get_current_active_user
from app.models import User

router = APIRouter(prefix="/sales-orders", tags=["销售订单"])


def generate_order_no() -> str:
    """生成订单号"""
    today = date.today().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"SO{today}{random_str}"


@router.get("", response_model=SalesOrderListResponse)
def get_sales_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[SalesOrderStatusEnum] = None,
    customer_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取销售订单列表"""
    query = db.query(SalesOrder)
    
    if status:
        query = query.filter(SalesOrder.status == status)
    if customer_id:
        query = query.filter(SalesOrder.customer_id == customer_id)
    if start_date:
        query = query.filter(SalesOrder.order_date >= start_date)
    if end_date:
        query = query.filter(SalesOrder.order_date <= end_date)
    
    total = query.count()
    items = query.order_by(SalesOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {"total": total, "items": items}


@router.post("", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
def create_sales_order(
    order_data: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建销售订单"""
    # 检查客户是否存在
    customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客户不存在"
        )
    
    # 生成订单号
    order_no = generate_order_no()
    
    # 计算总金额
    total_amount = sum(item.quantity * item.unit_price for item in order_data.items)
    
    # 创建订单
    db_order = SalesOrder(
        order_no=order_no,
        customer_id=order_data.customer_id,
        order_date=order_data.order_date,
        delivery_date=order_data.delivery_date,
        total_amount=total_amount,
        remark=order_data.remark,
        status=SalesOrderStatusEnum.DRAFT
    )
    db.add(db_order)
    db.flush()  # 获取ID
    
    # 创建订单明细
    for item_data in order_data.items:
        # 检查产品是否存在
        product = db.query(Material).filter(Material.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"产品不存在 (ID: {item_data.product_id})"
            )
        
        item_amount = item_data.quantity * item_data.unit_price
        db_item = SalesOrderItem(
            order_id=db_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            amount=item_amount
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    
    return db_order


@router.get("/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取销售订单详情"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    return order


@router.put("/{order_id}", response_model=SalesOrderResponse)
def update_sales_order(
    order_id: UUID,
    order_data: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新销售订单"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    for key, value in order_data.dict(exclude_unset=True).items():
        setattr(order, key, value)
    
    db.commit()
    db.refresh(order)
    
    return order


@router.put("/{order_id}/status", response_model=SalesOrderResponse)
def update_order_status(
    order_id: UUID,
    status: SalesOrderStatusEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新订单状态"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    order.status = status
    db.commit()
    db.refresh(order)
    
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除销售订单"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 只有草稿状态的订单可以删除
    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的订单可以删除"
        )
    
    db.delete(order)
    db.commit()
    
    return None