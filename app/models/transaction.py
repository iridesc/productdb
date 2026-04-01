from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, Enum, ForeignKey, Date
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


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    contact = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sales_orders = relationship("SalesOrder", back_populates="customer")


class SalesOrderStatusEnum(str, enum.Enum):
    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待处理
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(100), nullable=True)
    customer_address = Column(String(200), nullable=True)
    express_no = Column(String(50), nullable=True)
    express_confirmed = Column(Boolean, default=False)
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=True)
    status = Column(Enum(SalesOrderStatusEnum), default=SalesOrderStatusEnum.DRAFT)
    total_amount = Column(Numeric(12, 2), default=0)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="sales_orders")
    items = relationship("SalesOrderItem", back_populates="order", cascade="all, delete-orphan")
    production_orders = relationship("ProductionOrder", back_populates="sales_order")


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("sales_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("SalesOrder", back_populates="items")
    product = relationship("Material")


class ProductionOrderStatusEnum(str, enum.Enum):
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
    completed_quantity = Column(Numeric(10, 2), default=0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(Enum(ProductionOrderStatusEnum), default=ProductionOrderStatusEnum.PENDING)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sales_order = relationship("SalesOrder", back_populates="production_orders")
    product = relationship("Material")
    items = relationship("ProductionOrderItem", back_populates="production_order", cascade="all, delete-orphan")


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


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)