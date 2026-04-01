from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from app.database import get_db
from app.models import (
    SalesOrder,
    SalesOrderItem,
    SalesOrderStatusEnum,
    Customer,
    Material,
    InventoryTransaction,
    InventoryTransactionTypeEnum,
    User,
)
from app.schemas import (
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderResponse,
    SalesOrderListResponse,
    SalesOrderItemCreate,
    SalesOrderItemResponse,
)
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/sales-orders", tags=["销售订单"])


def generate_order_no(db: Session) -> str:
    """生成订单号"""
    total_order_count = db.query(SalesOrder).count() + 1
    return f"S-{total_order_count:03d}"


@router.get("", response_model=SalesOrderListResponse)
def get_sales_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[SalesOrderStatusEnum] = None,
    customer_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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
    items = (
        query.order_by(SalesOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"total": total, "items": items}


@router.post("", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
def create_sales_order(
    order_data: SalesOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建销售订单（草稿状态）"""
    customer = None
    if order_data.customer_id:
        customer = (
            db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="客户不存在"
            )

    order_no = generate_order_no(db)

    total_amount = 0
    if order_data.items:
        total_amount = sum(item.quantity * item.unit_price for item in order_data.items)

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
        status=SalesOrderStatusEnum.DRAFT,
    )
    db.add(db_order)
    db.flush()

    if order_data.items:
        for item_data in order_data.items:
            product = (
                db.query(Material).filter(Material.id == item_data.product_id).first()
            )
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"产品不存在 (ID: {item_data.product_id})",
                )

            item_amount = item_data.quantity * item_data.unit_price
            db_item = SalesOrderItem(
                order_id=db_order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=item_amount,
                is_confirmed=False,
            )
            db.add(db_item)

    db.commit()
    db.refresh(db_order)
    return db_order


@router.get("/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取销售订单详情"""
    order = (
        db.query(SalesOrder)
        .options(
            selectinload(SalesOrder.items).selectinload(
                SalesOrderItem.product
            ).selectinload(Material.images)
        )
        .filter(SalesOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    return order


@router.put("/{order_id}", response_model=SalesOrderResponse)
def update_sales_order(
    order_id: UUID,
    order_data: SalesOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新销售订单（仅草稿状态可编辑）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿状态的订单可以编辑"
        )

    if order_data.customer_id and order_data.customer_id != order.customer_id:
        customer = (
            db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        )
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="客户不存在"
            )

    update_data = order_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    if order_data.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            order.customer_name = customer.name

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除销售订单（仅草稿状态可删除）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿状态的订单可以删除"
        )

    db.delete(order)
    db.commit()
    return None


@router.put("/{order_id}/items", response_model=SalesOrderResponse)
def update_sales_order_items(
    order_id: UUID,
    items: List[SalesOrderItemCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新销售订单商品（仅草稿状态可编辑）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的订单可以编辑商品",
        )

    db.query(SalesOrderItem).filter(SalesOrderItem.order_id == order_id).delete()

    for item_data in items:
        product = db.query(Material).filter(Material.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"产品不存在 (ID: {item_data.product_id})",
            )

        item_amount = item_data.quantity * item_data.unit_price
        db_item = SalesOrderItem(
            order_id=order_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            amount=item_amount,
            is_confirmed=False,
        )
        db.add(db_item)

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
    current_user: User = Depends(get_current_active_user),
):
    """发布销售订单（草稿 -> 待处理）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿状态的订单可以发布"
        )

    errors = []

    if not order.express_no:
        errors.append("物流单号不能为空")

    if not order.items or len(order.items) == 0:
        errors.append("订单至少需要一个物料")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "订单信息不完整", "fields": errors},
        )

    order.status = SalesOrderStatusEnum.PENDING
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/items/{item_id}/confirm", response_model=SalesOrderResponse)
def confirm_sales_order_item(
    order_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """确认分配物料（扣减库存）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待处理状态的订单可以分配物料"
        )

    item = db.query(SalesOrderItem).filter(
        SalesOrderItem.id == item_id,
        SalesOrderItem.order_id == order_id,
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单明细不存在")

    if item.is_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="该物料已分配"
        )

    product = db.query(Material).filter(Material.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")

    if product.current_stock < item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"库存不足：{product.name} 当前库存 {product.current_stock}，需要 {item.quantity}",
        )

    before_stock = product.current_stock
    product.current_stock -= item.quantity
    item.is_confirmed = True

    transaction = InventoryTransaction(
        material_id=product.id,
        transaction_type=InventoryTransactionTypeEnum.SALES_OUT,
        quantity=item.quantity,
        before_quantity=before_stock,
        after_quantity=product.current_stock,
        reference_type="sales_order",
        reference_id=order_id,
        operator=current_user.username,
        remark=f"销售订单 {order.order_no} 分配物料",
    )
    db.add(transaction)

    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/confirm-express", response_model=SalesOrderResponse)
def confirm_express(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """确认物流单号"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待处理状态的订单可以确认物流"
        )

    if order.express_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="物流单号已确认"
        )

    order.express_confirmed = True
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/complete", response_model=SalesOrderResponse)
def complete_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """完成销售订单"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待处理状态的订单可以完成"
        )

    unconfirmed_items = [item for item in order.items if not item.is_confirmed]
    if unconfirmed_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"还有 {len(unconfirmed_items)} 个物料未分配，请先分配所有物料",
        )

    if not order.express_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="请先确认物流单号"
        )

    order.status = SalesOrderStatusEnum.COMPLETED
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/cancel", response_model=SalesOrderResponse)
def cancel_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """取消销售订单（仅待处理状态可取消）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status not in (SalesOrderStatusEnum.DRAFT, SalesOrderStatusEnum.PENDING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿或待处理状态的订单可以取消"
        )

    if order.status == SalesOrderStatusEnum.PENDING:
        for item in order.items:
            if item.is_confirmed:
                product = db.query(Material).filter(Material.id == item.product_id).first()
                if product:
                    before_stock = product.current_stock
                    product.current_stock += item.quantity
                    transaction = InventoryTransaction(
                        material_id=product.id,
                        transaction_type=InventoryTransactionTypeEnum.ADJUSTMENT,
                        quantity=item.quantity,
                        before_quantity=before_stock,
                        after_quantity=product.current_stock,
                        reference_type="sales_order_cancel",
                        reference_id=order_id,
                        operator=current_user.username,
                        remark=f"取消销售订单 {order.order_no}，退回物料",
                    )
                    db.add(transaction)

    order.status = SalesOrderStatusEnum.CANCELLED
    db.commit()
    db.refresh(order)
    return order
