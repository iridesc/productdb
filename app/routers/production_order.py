import os
import uuid as uuid_lib

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import random

from app.database import get_db
from app.models import (
    ProductionOrder, ProductionOrderImage, ProductionOrderItem, ProductionOrderStatusEnum,
    SalesOrder, Material, BOM, User, MaterialImage,
    InventoryTransaction, InventoryTransactionTypeEnum,
)
from app.schemas import (
    ProductionOrderCreate, ProductionOrderImageResponse, ProductionOrderUpdate,
    ProductionOrderResponse, ProductionOrderListResponse, YieldUpdate,
)
from app.utils.auth import get_current_active_user, require_permissions

router = APIRouter(prefix="/production-orders", tags=["生产订单"])

UPLOAD_DIR = "/app/uploads/images"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def generate_production_no(db: Session) -> str:
    """生成生产单号: P-YYMMDD-XXXX"""
    date_part = datetime.utcnow().strftime("%y%m%d")
    rand_part = f"{random.randint(0, 9999):04d}"
    return f"P-{date_part}-{rand_part}"


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
    query = db.query(ProductionOrder).options(
        selectinload(ProductionOrder.product).selectinload(Material.images),
        selectinload(ProductionOrder.items).selectinload(ProductionOrderItem.material).selectinload(Material.images)
    )

    # 无创建权限的用户仅看到待生产订单
    if not current_user.is_superuser and not current_user.can_create_production:
        query = query.filter(
            ProductionOrder.status.in_([
                ProductionOrderStatusEnum.PENDING,
            ])
        )

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
    current_user: User = Depends(require_permissions("can_create_production")),
):
    """创建生产订单（草稿状态）"""
    # 检查产品是否存在
    product = db.query(Material).filter(Material.id == order_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )

    # 校验生产数量不超过1000
    if order_data.quantity > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"生产数量不得超过1000，当前数量: {order_data.quantity}"
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
    order_no = generate_production_no(db)

    # 创建生产订单（草稿状态，不扣库存）
    db_order = ProductionOrder(
        order_no=order_no,
        sales_order_id=order_data.sales_order_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity,
        start_date=order_data.start_date,
        end_date=order_data.end_date,
        remark=order_data.remark,
        status=ProductionOrderStatusEnum.DRAFT
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
    order = db.query(ProductionOrder).options(
        selectinload(ProductionOrder.product).selectinload(Material.images),
        selectinload(ProductionOrder.items).selectinload(ProductionOrderItem.material).selectinload(Material.images),
        selectinload(ProductionOrder.images),
    ).filter(ProductionOrder.id == order_id).first()
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
    current_user: User = Depends(require_permissions("can_create_production")),
):
    """更新生产订单（仅草稿状态可编辑，修改产品/数量时重新生成BOM物料）"""
    order = db.query(ProductionOrder).options(
        selectinload(ProductionOrder.items),
    ).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )

    if order.status != ProductionOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的订单可以编辑"
        )

    # 检查是否需要重新生成 BOM
    product_changed = (
        order_data.product_id is not None
        and order_data.product_id != order.product_id
    )
    quantity_changed = (
        order_data.quantity is not None
        and float(order_data.quantity) != float(order.quantity)
    )

    # 更新基础字段
    update_data = order_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)

    db.flush()

    # 如果产品或数量有变化，重新生成 BOM 物料需求
    if product_changed or quantity_changed:
        # 验证新产品存在
        if product_changed:
            new_product = db.query(Material).filter(
                Material.id == order_data.product_id
            ).first()
            if not new_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="产品不存在"
                )

        # 删除旧的物料需求
        for item in order.items:
            db.delete(item)
        db.flush()

        # 基于新产品/新数量重新生成 BOM
        target_product_id = order_data.product_id if product_changed else order.product_id
        target_quantity = order_data.quantity if quantity_changed else order.quantity

        boms = db.query(BOM).filter(BOM.product_id == target_product_id).all()
        for bom in boms:
            required_quantity = float(target_quantity) * float(bom.quantity) * (1 + float(bom.scrap_rate) / 100)
            db_item = ProductionOrderItem(
                production_order_id=order.id,
                material_id=bom.material_id,
                quantity=required_quantity
            )
            db.add(db_item)

    db.commit()
    db.refresh(order)

    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("can_create_production")),
):
    """删除生产订单（仅草稿状态可删除）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )

    if order.status != ProductionOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的订单可以删除"
        )

    db.delete(order)
    db.commit()

    return None


@router.put("/{order_id}/publish", response_model=ProductionOrderResponse)
def publish_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("can_create_production")),
):
    """发布生产订单：校验物料库存并扣减（草稿 → 待生产）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产订单不存在")

    if order.status != ProductionOrderStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿状态的订单可以发布"
        )

    # 如果订单还没有物料需求（BOM 在订单创建之后才设置），自动生成
    if not order.items or len(order.items) == 0:
        boms = db.query(BOM).filter(BOM.product_id == order.product_id).all()
        if not boms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="订单没有物料需求，无法发布"
            )
        for bom in boms:
            required_quantity = order.quantity * bom.quantity * (1 + bom.scrap_rate / 100)
            db_item = ProductionOrderItem(
                production_order_id=order.id,
                material_id=bom.material_id,
                quantity=required_quantity
            )
            db.add(db_item)
        db.flush()
        db.refresh(order)

    # 逐个检查 BOM 物料库存是否充足
    shortages = []
    for item in order.items:
        material = db.query(Material).filter(Material.id == item.material_id).first()
        if not material:
            shortages.append({
                "material_id": str(item.material_id),
                "material_name": "未知物料",
                "current_stock": 0,
                "required": float(item.quantity),
            })
        elif material.current_stock < item.quantity:
            shortages.append({
                "material_id": str(material.id),
                "material_name": material.name,
                "material_code": material.code,
                "current_stock": float(material.current_stock),
                "required": float(item.quantity),
            })

    if shortages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "物料库存不足", "shortages": shortages},
        )

    # 全部充足：逐个扣减物料库存并生成流水
    for item in order.items:
        material = db.query(Material).filter(Material.id == item.material_id).first()
        before_stock = material.current_stock
        material.current_stock -= item.quantity

        transaction = InventoryTransaction(
            material_id=material.id,
            transaction_type=InventoryTransactionTypeEnum.PRODUCTION_OUT,
            quantity=item.quantity,
            before_quantity=before_stock,
            after_quantity=material.current_stock,
            reference_type="production_order",
            reference_id=order_id,
            operator=current_user.username,
            remark=f"生产订单 {order.order_no} 发布，扣减物料",
        )
        db.add(transaction)

    order.status = ProductionOrderStatusEnum.PENDING
    db.commit()
    db.refresh(order)

    return order


@router.put("/{order_id}/start", response_model=ProductionOrderResponse)
def start_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("can_manage_production")),
):
    """已废弃：状态机已简化，待生产订单可直接进行物料检查、产出确认、报工完成，无需开工步骤"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产订单不存在")

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待生产状态的订单可以操作"
        )

    # 开工步骤已移除，状态不变，直接返回订单
    return order


@router.put("/{order_id}/complete", response_model=ProductionOrderResponse)
def complete_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("can_manage_production")),
):
    """报工完成：成品入库（待生产 → 已完成）"""
    order = db.query(ProductionOrder).options(
        selectinload(ProductionOrder.items),
        selectinload(ProductionOrder.images),
    ).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产订单不存在")

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待生产状态的订单可以报工完成"
        )

    # 检查所有物料已分配
    unchecked = [item for item in order.items if item.consumed_quantity == 0]
    if unchecked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"还有 {len(unchecked)} 个物料未检查，请先完成物料检查",
        )

    # 检查产出数量已确认（允许 0，表示无产出）
    if order.completed_quantity is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先确认产出数量",
        )

    # 检查产品图已上传
    if not order.images or len(order.images) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先上传产品图片",
        )

    # 成品入库
    product = db.query(Material).filter(Material.id == order.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")

    before_stock = product.current_stock
    product.current_stock += order.completed_quantity

    transaction = InventoryTransaction(
        material_id=product.id,
        transaction_type=InventoryTransactionTypeEnum.PRODUCTION_IN,
        quantity=order.completed_quantity,
        before_quantity=before_stock,
        after_quantity=product.current_stock,
        reference_type="production_order",
        reference_id=order_id,
        operator=current_user.username,
        remark=f"生产订单 {order.order_no} 完成，成品入库",
    )
    db.add(transaction)

    order.status = ProductionOrderStatusEnum.COMPLETED
    db.commit()
    db.refresh(order)

    return order



@router.put("/{order_id}/cancel", response_model=ProductionOrderResponse)
def cancel_production_order(
    order_id: UUID,
    return_inventory: bool = Query(True, description="是否退回已扣物料库存"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("is_superuser")),
):
    """取消生产订单（仅管理员，可选是否退回库存）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产订单不存在")

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待生产状态的订单可以取消"
        )

    if return_inventory:
        # 退回已扣物料库存
        for item in order.items:
            material = db.query(Material).filter(Material.id == item.material_id).first()
            if material:
                before_stock = material.current_stock
                material.current_stock += item.quantity

                transaction = InventoryTransaction(
                    material_id=material.id,
                    transaction_type=InventoryTransactionTypeEnum.ADJUSTMENT,
                    quantity=item.quantity,
                    before_quantity=before_stock,
                    after_quantity=material.current_stock,
                    reference_type="production_order_cancel",
                    reference_id=order_id,
                    operator=current_user.username,
                    remark=f"取消生产订单 {order.order_no}，退回物料",
                )
                db.add(transaction)

    order.status = ProductionOrderStatusEnum.CANCELLED
    db.commit()
    db.refresh(order)

    return order


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
            "material_id": str(material.id) if material else str(item.material_id),
            "material_code": material.code if material else "未知",
            "material_name": material.name if material else "未知物料",
            "required_quantity": float(item.quantity),
            "consumed_quantity": float(item.consumed_quantity),
            "current_stock": float(material.current_stock) if material else 0,
            "is_sufficient": material.current_stock >= item.quantity if material else False
        })

    return result


@router.put("/{order_id}/yield", response_model=ProductionOrderResponse)
def set_production_yield(
    order_id: UUID,
    yield_data: YieldUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """确认生产产出数量"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待生产状态的订单可以确认产出"
        )

    if yield_data.completed_quantity > order.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"产出数量不得超过计划数量 {order.quantity}"
        )

    order.completed_quantity = yield_data.completed_quantity
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/images", response_model=ProductionOrderImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_production_order_image(
    order_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """上传生产订单产品图（仅生产中状态）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待生产状态的订单可以上传图片"
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
        db.query(ProductionOrderImage.sort_order)
        .filter(ProductionOrderImage.order_id == order_id)
        .order_by(ProductionOrderImage.sort_order.desc())
        .first()
    )
    next_sort = (max_sort[0] + 1) if max_sort else 0

    image = ProductionOrderImage(
        order_id=order_id,
        image_type="product_shipping",
        image_url=f"/api/v1/uploads/{unique_filename}",
        sort_order=next_sort,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return image


@router.get("/{order_id}/images", response_model=List[ProductionOrderImageResponse])
def get_production_order_images(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取生产订单产品图列表"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")

    images = (
        db.query(ProductionOrderImage)
        .filter(ProductionOrderImage.order_id == order_id)
        .order_by(ProductionOrderImage.sort_order)
        .all()
    )
    return images


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_order_image(
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除产品图"""
    image = db.query(ProductionOrderImage).filter(ProductionOrderImage.id == image_id).first()
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


@router.put("/{order_id}/items/{item_id}/distribute", response_model=ProductionOrderResponse)
def distribute_production_item(
    order_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记物料已分配（库存已在开工时扣减，此处仅记录消耗进度）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单不存在"
        )

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待生产状态的订单可以分配物料"
        )

    item = db.query(ProductionOrderItem).filter(
        ProductionOrderItem.id == item_id,
        ProductionOrderItem.production_order_id == order_id,
    ).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生产订单物料不存在"
        )

    remaining = item.quantity - item.consumed_quantity
    if remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该物料已全部分配"
        )

    item.consumed_quantity = item.quantity
    db.commit()
    db.refresh(order)
    return order
