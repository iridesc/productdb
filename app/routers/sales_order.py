from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import random
import string

from database import get_db
from models import SalesOrder, SalesOrderItem, SalesOrderStatusEnum, Customer, Material
from schemas import (
    SalesOrderCreate, SalesOrderUpdate, SalesOrderResponse, SalesOrderListResponse,
    SalesOrderItemCreate, SalesOrderItemResponse
)
from utils.auth import get_current_active_user
from models import User

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
    """创建销售订单（草稿状态）"""
    # 如果提供了customer_id，检查客户是否存在
    customer = None
    if order_data.customer_id:
        customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="客户不存在"
            )
    
    # 生成订单号
    order_no = generate_order_no()
    
    # 计算总金额
    total_amount = 0
    if order_data.items:
        total_amount = sum(item.quantity * item.unit_price for item in order_data.items)
    
    # 创建订单（草稿状态）
    db_order = SalesOrder(
        order_no=order_no,
        customer_id=order_data.customer_id,
        customer_name=order_data.customer_name or (customer.name if customer else None),
        customer_address=order_data.customer_address,
        express_no=order_data.express_no,
        order_date=order_data.order_date,
        delivery_date=order_data.delivery_date,
        total_amount=total_amount,
        remark=order_data.remark,
        status=SalesOrderStatusEnum.DRAFT
    )
    db.add(db_order)
    db.flush()  # 获取ID
    
    # 创建订单明细（如果有）
    if order_data.items:
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
                amount=item_amount,
                is_confirmed=False
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
    """更新销售订单（仅草稿状态可编辑）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 只有草稿状态的订单可以编辑
    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的订单可以编辑"
        )
    
    # 如果提供了customer_id且与当前不同，检查新客户是否存在
    if order_data.customer_id and order_data.customer_id != order.customer_id:
        customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="客户不存在"
            )
    
    # 更新字段
    update_data = order_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)
    
    # 如果提供了customer_id，同步更新customer_name
    if order_data.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            order.customer_name = customer.name
    
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


@router.put("/{order_id}/items", response_model=SalesOrderResponse)
def update_sales_order_items(
    order_id: UUID,
    items: List[SalesOrderItemCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新销售订单商品（仅草稿状态可编辑）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 只有草稿状态的订单可以编辑商品
    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的订单可以编辑商品"
        )

    # 删除旧的商品
    db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order_id).delete()

    # 添加新的商品
    for item_data in items:
        # 检查产品是否存在
        product = db.query(Material).filter(Material.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"产品不存在 (ID: {item_data.product_id})"
            )

        item_amount = item_data.quantity * item_data.unit_price
        db_item = SalesOrderItem(
            order_id=order_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            amount=item_amount,
            is_confirmed=False
        )
        db.add(db_item)

    # 更新订单总金额
    total_amount = sum(item.quantity * item.unit_price for item in items)
    order.total_amount = total_amount
    order.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return order


@router.put("/{order_id}/publish", response_model=SalesOrderResponse)
def publish_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发布销售订单（草稿 -> 已确认）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 只有草稿状态的订单可以发布
    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的订单可以发布"
        )
    
    # 校验订单完整性
    errors = []
    
    # 1. 客户地址必填
    if not order.customer_address:
        errors.append("客户地址不能为空")
    
    # 2. 快递单号必填
    if not order.express_no:
        errors.append("快递单号不能为空")
    
    # 3. 至少有一个商品
    if not order.items or len(order.items) == 0:
        errors.append("订单至少需要一个商品")
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "订单信息不完整，请补充以下信息",
                "fields": errors
            }
        )
    
    # 发布订单
    order.status = SalesOrderStatusEnum.CONFIRMED
    db.commit()
    db.refresh(order)
    
    return order