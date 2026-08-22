from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, Enum, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class BOM(Base):
    __tablename__ = "boms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    quantity = Column(Numeric(10, 4), nullable=False, default=1)
    scrap_rate = Column(Numeric(5, 2), default=0)  # 损耗率 %
    is_optional = Column(Boolean, default=False)
    note = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Material", back_populates="product_boms", foreign_keys=[product_id])
    material = relationship("Material", back_populates="bom_items", foreign_keys=[material_id])



class SalesOrderStatusEnum(str, enum.Enum):
    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待处理
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(20), unique=True, nullable=False, index=True)
    customer_info = Column(Text, nullable=True)
    express_no = Column(String(50), nullable=True)
    express_confirmed = Column(Boolean, default=False)
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    status = Column(Enum(SalesOrderStatusEnum), default=SalesOrderStatusEnum.DRAFT)
    total_amount = Column(Numeric(15, 2), default=0)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete-orphan")
    images = relationship("SalesOrderImage", back_populates="order", cascade="all, delete-orphan")
    production_orders = relationship("ProductionOrder", back_populates="sales_order")


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Material")


class SalesOrderImageType(str, enum.Enum):
    PRODUCT_SHIPPING = "product_shipping"  # 产品发货图片
    LOGISTICS = "logistics"  # 物流凭证图片


class SalesOrderImage(Base):
    __tablename__ = "sales_order_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sales_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_type = Column(Enum(SalesOrderImageType), nullable=False)
    image_url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("SalesOrder", back_populates="images")


class ProductionOrderStatusEnum(str, enum.Enum):
    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待生产
    IN_PRODUCTION = "in_production"  # 生产中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(20), unique=True, nullable=False, index=True)
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey("sales_orders.id"), nullable=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    completed_quantity = Column(Numeric(10, 2), nullable=True, default=None)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(Enum(ProductionOrderStatusEnum), default=ProductionOrderStatusEnum.DRAFT)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sales_order = relationship("SalesOrder", back_populates="production_orders")
    product = relationship("Material")
    items = relationship("ProductionOrderItem", back_populates="production_order", cascade="all, delete-orphan")
    images = relationship("ProductionOrderImage", back_populates="order", cascade="all, delete-orphan")


class ProductionOrderItem(Base):
    __tablename__ = "production_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)  # 需求数量
    consumed_quantity = Column(Numeric(10, 2), default=0)  # 已消耗数量
    created_at = Column(DateTime, default=datetime.utcnow)

    production_order = relationship("ProductionOrder", back_populates="items")
    material = relationship("Material")


class ProductionOrderImage(Base):
    __tablename__ = "production_order_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("production_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_type = Column(String(50), nullable=False, default="product_shipping")
    image_url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("ProductionOrder", back_populates="images")


class InventoryTransactionTypeEnum(str, enum.Enum):
    PURCHASE = "purchase"  # 采购入库
    PRODUCTION_IN = "production_in"  # 生产入库
    PRODUCTION_OUT = "production_out"  # 生产领料
    SALES_OUT = "sales_out"  # 销售出库
    ADJUSTMENT = "adjustment"  # 调整
    TRANSFER = "transfer"  # 转账


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    transaction_type = Column(Enum(InventoryTransactionTypeEnum), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    before_quantity = Column(Numeric(10, 2), nullable=False)
    after_quantity = Column(Numeric(10, 2), nullable=False)
    reference_type = Column(String(50), nullable=True)  # 来源类型：订单号等
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    operator = Column(String(50), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("Material")


class Role(Base):
    __tablename__ = "roles"

    code = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_code = Column(String(20), ForeignKey("roles.code"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="roles")
    role = relationship("Role")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    can_view_dashboard = Column(Boolean, default=True)
    can_manage_materials = Column(Boolean, default=True)
    can_manage_sales = Column(Boolean, default=True)
    can_manage_production = Column(Boolean, default=True)
    can_manage_inventory = Column(Boolean, default=True)
    can_manage_users = Column(Boolean, default=False)
    can_create_sales = Column(Boolean, default=False)
    can_create_production = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class SystemToken(Base):
    """Long-lived API token used by trusted system integrations such as MCP."""

    __tablename__ = "system_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    token_prefix = Column(String(16), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User")
