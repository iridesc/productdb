from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from app.models.material import MaterialCategoryEnum
from app.models.transaction import SalesOrderStatusEnum, ProductionOrderStatusEnum, InventoryTransactionTypeEnum


# ==================== 基础 Schema ====================

class MaterialCategoryBase(BaseModel):
    name: str = Field(..., max_length=50)
    code: str = Field(..., max_length=20)
    parent_id: Optional[UUID] = None


class MaterialCategoryCreate(MaterialCategoryBase):
    pass


class MaterialCategoryResponse(MaterialCategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 物料 Schema ====================

class MaterialBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    category: MaterialCategoryEnum
    unit: str = Field(default="个", max_length=20)
    specification: Optional[str] = Field(None, max_length=200)
    safety_stock: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    current_stock: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    price: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    description: Optional[str] = None
    is_active: bool = True
    category_id: Optional[UUID] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    specification: Optional[str] = None
    safety_stock: Optional[Decimal] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[UUID] = None


class MaterialResponse(MaterialBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    category_info: Optional[MaterialCategoryResponse] = None

    class Config:
        from_attributes = True


class MaterialListResponse(BaseModel):
    total: int
    items: List[MaterialResponse]


# ==================== BOM Schema ====================

class BOMBase(BaseModel):
    product_id: UUID
    material_id: UUID
    quantity: Decimal = Field(..., max_digits=10, decimal_places=4)
    scrap_rate: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    is_optional: bool = False
    note: Optional[str] = Field(None, max_length=200)


class BOMCreate(BOMBase):
    pass


class BOMResponse(BOMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    product: MaterialResponse
    material: MaterialResponse

    class Config:
        from_attributes = True


class BOMWithProductResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    product_code: str
    material_id: UUID
    material_name: str
    material_code: str
    quantity: Decimal
    scrap_rate: Decimal
    is_optional: bool
    note: Optional[str]

    class Config:
        from_attributes = True


# ==================== 客户 Schema ====================

class CustomerBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    contact: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    total: int
    items: List[CustomerResponse]


# ==================== 销售订单 Schema ====================

class SalesOrderItemBase(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(..., max_digits=10, decimal_places=2)
    unit_price: Decimal = Field(..., max_digits=10, decimal_places=2)


class SalesOrderItemCreate(SalesOrderItemBase):
    pass


class SalesOrderItemResponse(SalesOrderItemBase):
    id: UUID
    amount: Decimal
    product: MaterialResponse
    created_at: datetime

    class Config:
        from_attributes = True


class SalesOrderBase(BaseModel):
    customer_id: UUID
    order_date: date
    delivery_date: Optional[date] = None
    remark: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    items: List[SalesOrderItemCreate]


class SalesOrderUpdate(BaseModel):
    delivery_date: Optional[date] = None
    status: Optional[SalesOrderStatusEnum] = None
    remark: Optional[str] = None


class SalesOrderResponse(SalesOrderBase):
    id: UUID
    order_no: str
    status: SalesOrderStatusEnum
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    customer: CustomerResponse
    items: List[SalesOrderItemResponse] = []

    class Config:
        from_attributes = True


class SalesOrderListResponse(BaseModel):
    total: int
    items: List[SalesOrderResponse]


# ==================== 生产订单 Schema ====================

class ProductionOrderItemBase(BaseModel):
    material_id: UUID
    quantity: Decimal = Field(..., max_digits=10, decimal_places=2)


class ProductionOrderItemCreate(ProductionOrderItemBase):
    pass


class ProductionOrderItemResponse(ProductionOrderItemBase):
    id: UUID
    consumed_quantity: Decimal
    material: MaterialResponse
    created_at: datetime

    class Config:
        from_attributes = True


class ProductionOrderBase(BaseModel):
    sales_order_id: Optional[UUID] = None
    product_id: UUID
    quantity: Decimal = Field(..., max_digits=10, decimal_places=2)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = None


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProductionOrderStatusEnum] = None
    remark: Optional[str] = None


class ProductionOrderResponse(ProductionOrderBase):
    id: UUID
    order_no: str
    completed_quantity: Decimal
    status: ProductionOrderStatusEnum
    created_at: datetime
    updated_at: datetime
    product: MaterialResponse
    sales_order: Optional[SalesOrderResponse] = None
    items: List[ProductionOrderItemResponse] = []

    class Config:
        from_attributes = True


class ProductionOrderListResponse(BaseModel):
    total: int
    items: List[ProductionOrderResponse]


# ==================== 库存 Schema ====================

class InventoryTransactionBase(BaseModel):
    material_id: UUID
    transaction_type: InventoryTransactionTypeEnum
    quantity: Decimal
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    operator: Optional[str] = None
    remark: Optional[str] = None


class InventoryTransactionCreate(InventoryTransactionBase):
    pass


class InventoryTransactionResponse(InventoryTransactionBase):
    id: UUID
    before_quantity: Decimal
    after_quantity: Decimal
    created_at: datetime
    material: MaterialResponse

    class Config:
        from_attributes = True


class InventoryResponse(BaseModel):
    material_id: UUID
    material_code: str
    material_name: str
    category: MaterialCategoryEnum
    unit: str
    current_stock: Decimal
    safety_stock: Decimal

    class Config:
        from_attributes = True


class InventoryListResponse(BaseModel):
    total: int
    items: List[InventoryResponse]


# ==================== 用户 Schema ====================

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: str = Field(..., max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 认证 Schema ====================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str