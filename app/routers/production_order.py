from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
import random

from app.database import get_db
from app.models import (
    ProductionOrder, ProductionOrderItem, ProductionOrderStatusEnum,
    SalesOrder, Material, BOM, User,
    InventoryTransaction, InventoryTransactionTypeEnum,
)
from app.schemas import (
    ProductionOrderCreate, ProductionOrderUpdate, ProductionOrderResponse,
    ProductionOrderListResponse
)
from app.utils.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/production-orders", tags=["生产订单"])


def generate_production_no(db: Session) -> str:
    """生成生产单号: P-YYMMDD-XXXX"""
    date_part = datetime.utcnow().strftime("%y%m%d")
    rand_part = f"{random.randint(0, 9999):04d}"
    return f"P-{date_part}-{rand_part}"


def _get_user_role_codes(user: User) -> set:
    """获取用户的角色编码集合"""
    return {ur.role_code for ur in user.roles}


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
    """获取生产订单列表（按角色过滤）"""
    query = db.query(ProductionOrder)

    # 角色过滤：纯工人只能看到 pending + in_production
    role_codes = _get_user_role_codes(current_user)
    is_worker_only = "worker" in role_codes and "operator" not in role_codes and "admin" not in role_codes
    if is_worker_only:
        query = query.filter(
            ProductionOrder.status.in_([
                ProductionOrderStatusEnum.PENDING,
                ProductionOrderStatusEnum.IN_PRODUCTION,
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
    current_user: User = Depends(require_roles("operator", "admin")),
):
    """创建生产订单（草稿状态）"""
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
    current_user: User = Depends(require_roles("operator", "admin")),
):
    """更新生产订单（仅草稿状态可编辑）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
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

    for key, value in order_data.dict(exclude_unset=True).items():
        setattr(order, key, value)

    db.commit()
    db.refresh(order)

    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("operator", "admin")),
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
    current_user: User = Depends(require_roles("operator", "admin")),
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
    current_user: User = Depends(require_roles("worker", "admin")),
):
    """开工：将订单从待生产转为生产中（库存无变化）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产订单不存在")

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待生产状态的订单可以开工"
        )

    order.status = ProductionOrderStatusEnum.IN_PRODUCTION
    db.commit()
    db.refresh(order)

    return order


@router.put("/{order_id}/complete", response_model=ProductionOrderResponse)
def complete_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("worker", "admin")),
):
    """报工完成：成品入库（生产中 → 已完成）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产订单不存在")

    if order.status != ProductionOrderStatusEnum.IN_PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有生产中的订单可以报工完成"
        )

    # 成品入库
    product = db.query(Material).filter(Material.id == order.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")

    before_stock = product.current_stock
    product.current_stock += order.quantity

    transaction = InventoryTransaction(
        material_id=product.id,
        transaction_type=InventoryTransactionTypeEnum.PRODUCTION_IN,
        quantity=order.quantity,
        before_quantity=before_stock,
        after_quantity=product.current_stock,
        reference_type="production_order",
        reference_id=order_id,
        operator=current_user.username,
        remark=f"生产订单 {order.order_no} 完成，成品入库",
    )
    db.add(transaction)

    order.completed_quantity = order.quantity
    order.status = ProductionOrderStatusEnum.COMPLETED
    db.commit()
    db.refresh(order)

    return order


@router.put("/{order_id}/cancel", response_model=ProductionOrderResponse)
def cancel_production_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("operator", "admin")),
):
    """取消生产订单：退回已扣物料库存（仅待生产状态可取消，生产中不可取消）"""
    order = db.query(ProductionOrder).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="生产订单不存在")

    if order.status == ProductionOrderStatusEnum.IN_PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="生产中的订单不可取消"
        )

    if order.status != ProductionOrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只有待生产状态的订单可以取消"
        )

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
