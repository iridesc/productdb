import os
import uuid as uuid_lib

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from app.database import get_db
from app.models import (
    SalesOrder,
    SalesOrderImage,
    SalesOrderImageType,
    SalesOrderItem,
    SalesOrderStatusEnum,
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
    SalesOrderImageResponse,
    SalesOrderItemCreate,
    SalesOrderItemResponse,
)
from app.utils.auth import get_current_active_user, require_permissions

router = APIRouter(prefix="/sales-orders", tags=["销售订单"])

UPLOAD_DIR = "/app/uploads/images"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def generate_order_no(db: Session) -> str:
    """生成订单号（基于已有最大编号+1）"""
    last = db.query(SalesOrder.order_no).order_by(
        SalesOrder.order_no.desc()
    ).first()
    if last and last[0]:
        try:
            num = int(last[0].split('-')[1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"S-{num:03d}"


@router.get("", response_model=SalesOrderListResponse)
def get_sales_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[SalesOrderStatusEnum] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取销售订单列表"""
    query = db.query(SalesOrder).options(
        selectinload(SalesOrder.items).selectinload(SalesOrderItem.product)
    )


    # 无管理/创建权限的用户仅看到待处理和已完成的订单
    if not current_user.is_superuser and not current_user.can_create_sales:
        query = query.filter(
            SalesOrder.status.in_([
                SalesOrderStatusEnum.PENDING,
                SalesOrderStatusEnum.COMPLETED,
            ])
        )
    if status:
        query = query.filter(SalesOrder.status == status)
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
    # 校验每种产品数量不超过1000
    if order_data.items:
        for item in order_data.items:
            if item.quantity > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"每种产品数量不得超过1000，当前数量: {item.quantity}"
                )

    order_no = generate_order_no(db)

    total_amount = 0
    if order_data.items:
        total_amount = sum(item.quantity * item.unit_price for item in order_data.items)

    db_order = SalesOrder(
        order_no=order_no,
        customer_info=order_data.customer_info,
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
            ).selectinload(Material.images),
            selectinload(SalesOrder.images),
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

    update_data = order_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

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

    # 校验每种产品数量不超过1000
    for item in items:
        if item.quantity > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"每种产品数量不得超过1000，当前数量: {item.quantity}"
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
    """发布销售订单（草稿 -> 待处理），检查库存并一次性扣减"""
    order = db.query(SalesOrder).options(selectinload(SalesOrder.items)).filter(SalesOrder.id == order_id).first()
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

    # 检查所有物料库存
    for item in order.items:
        product = db.query(Material).filter(Material.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"产品不存在 (ID: {item.product_id})",
            )
        if product.current_stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"库存不足：{product.name} 当前库存 {product.current_stock}，需要 {item.quantity}",
            )

    # 一次性扣减所有物料库存
    for item in order.items:
        product = db.query(Material).filter(Material.id == item.product_id).first()
        before_stock = product.current_stock
        product.current_stock -= item.quantity

        transaction = InventoryTransaction(
            material_id=product.id,
            transaction_type=InventoryTransactionTypeEnum.SALES_OUT,
            quantity=item.quantity,
            before_quantity=before_stock,
            after_quantity=product.current_stock,
            reference_type="sales_order",
            reference_id=order_id,
            operator=current_user.username,
            remark=f"销售订单 {order.order_no} 锁定库存",
        )
        db.add(transaction)

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
    """确认分配物料（标记操作，库存已在发布时锁定）"""
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

    item.is_confirmed = True
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/images", response_model=SalesOrderImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_sales_order_image(
    order_id: UUID,
    file: UploadFile = File(...),
    image_type: SalesOrderImageType = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """上传销售订单凭证图片（仅待处理状态）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != SalesOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待处理状态的订单可以上传图片"
        )

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式，支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"图片太大({size_mb:.1f}MB)，请压缩到5MB以内"
        )

    ensure_upload_dir()

    unique_filename = f"{uuid_lib.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)

    with open(filepath, "wb") as f:
        f.write(content)

    max_sort = (
        db.query(SalesOrderImage.sort_order)
        .filter(SalesOrderImage.order_id == order_id)
        .order_by(SalesOrderImage.sort_order.desc())
        .first()
    )
    next_sort = (max_sort[0] + 1) if max_sort else 0

    image = SalesOrderImage(
        order_id=order_id,
        image_type=image_type,
        image_url=f"/api/v1/uploads/{unique_filename}",
        sort_order=next_sort,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    # 物流图片上传自动确认物流
    if image_type == SalesOrderImageType.LOGISTICS and not order.express_confirmed:
        order.express_confirmed = True
        db.commit()

    return image


@router.get("/{order_id}/images", response_model=List[SalesOrderImageResponse])
def get_sales_order_images(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取销售订单凭证图片列表"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    images = (
        db.query(SalesOrderImage)
        .filter(SalesOrderImage.order_id == order_id)
        .order_by(SalesOrderImage.image_type, SalesOrderImage.sort_order)
        .all()
    )
    return images


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_order_image(
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除凭证图片"""
    image = db.query(SalesOrderImage).filter(SalesOrderImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    try:
        filename = os.path.basename(image.image_url)
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

    db.delete(image)
    db.commit()

    return None


@router.put("/{order_id}/complete", response_model=SalesOrderResponse)
def complete_sales_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """完成销售订单"""
    order = (
        db.query(SalesOrder)
        .options(
            selectinload(SalesOrder.items),
            selectinload(SalesOrder.images),
        )
        .filter(SalesOrder.id == order_id)
        .first()
    )
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

    product_images = [
        img for img in order.images
        if img.image_type == SalesOrderImageType.PRODUCT_SHIPPING
    ]
    logistics_images = [
        img for img in order.images
        if img.image_type == SalesOrderImageType.LOGISTICS
    ]

    if not product_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传产品发货图片",
        )
    if not logistics_images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传物流凭证图片",
        )

    order.status = SalesOrderStatusEnum.COMPLETED
    db.commit()
    db.refresh(order)
    return order

@router.put("/{order_id}/cancel", response_model=SalesOrderResponse)
def cancel_sales_order(
    order_id: UUID,
    return_inventory: bool = Query(True, description="是否退回已锁定物料库存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("is_superuser")),
):
    """取消销售订单（仅管理员，可选是否退回库存）"""
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status not in (SalesOrderStatusEnum.DRAFT, SalesOrderStatusEnum.PENDING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿或待处理状态的订单可以取消"
        )

    if order.status == SalesOrderStatusEnum.PENDING and return_inventory:
        # 退回已扣减的物料库存
        for item in order.items:
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
