from pydantic import BaseModel, Field, computed_field
from pydantic import field_serializer
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from app.models.material import MaterialCategoryEnum
from app.models.transaction import (
    SalesOrderImageType,
    SalesOrderStatusEnum,
    ProductionOrderStatusEnum,
    InventoryTransactionTypeEnum,
)


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
    safety_stock: Decimal = Field(default=Decimal("0"))
    current_stock: Decimal = Field(default=Decimal("0"))
    price: Decimal = Field(default=Decimal("0"))
    sale_price: Decimal = Field(default=Decimal("0"))
    other_cost: Decimal = Field(default=Decimal("0"))
    description: Optional[str] = None
    is_active: bool = True
    category_id: Optional[UUID] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[MaterialCategoryEnum] = None
    unit: Optional[str] = None
    specification: Optional[str] = None
    safety_stock: Optional[Decimal] = None
    current_stock: Optional[Decimal] = None
    price: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    other_cost: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[UUID] = None


class MaterialResponse(MaterialBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    category_info: Optional[MaterialCategoryResponse] = None
    bom_cost: Optional[Decimal] = Field(default=Decimal("0"))
    total_cost: Optional[Decimal] = Field(default=Decimal("0"))
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class MaterialListResponse(BaseModel):
    total: int
    items: List[MaterialResponse]


# ==================== BOM Schema ====================


class BOMBase(BaseModel):
    product_id: UUID
    material_id: UUID
    quantity: Decimal = Field(...)
    scrap_rate: Decimal = Field(default=Decimal("0"))
    is_optional: bool = False
    note: Optional[str] = Field(None, max_length=200)


class BOMCreate(BOMBase):
    pass


class BOMUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    scrap_rate: Optional[Decimal] = None
    is_optional: Optional[bool] = None
    note: Optional[str] = None


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
    thumbnail_url: Optional[str] = None
    material_current_stock: Optional[Decimal] = None

    class Config:
        from_attributes = True


# ==================== 销售订单 Schema ====================


class SalesOrderItemBase(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(...)
    unit_price: Decimal = Field(...)


class SalesOrderItemCreate(SalesOrderItemBase):
    pass


class SalesOrderItemResponse(SalesOrderItemBase):
    id: UUID
    amount: Decimal
    product: MaterialResponse
    is_confirmed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SalesOrderImageResponse(BaseModel):
    id: UUID
    order_id: UUID
    image_type: SalesOrderImageType
    image_url: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class SalesOrderBase(BaseModel):
    customer_info: Optional[str] = Field(None, max_length=500)
    express_no: Optional[str] = None
    express_confirmed: Optional[bool] = None
    order_date: date
    delivery_date: Optional[date] = None
    remark: Optional[str] = None


class SalesOrderCreate(SalesOrderBase):
    items: Optional[List[SalesOrderItemCreate]] = None


class SalesOrderUpdate(BaseModel):
    customer_info: Optional[str] = None
    express_no: Optional[str] = None
    delivery_date: Optional[date] = None
    remark: Optional[str] = None


class SalesOrderResponse(SalesOrderBase):
    id: UUID
    order_no: str
    status: SalesOrderStatusEnum
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: List[SalesOrderItemResponse] = []
    images: List[SalesOrderImageResponse] = []

    class Config:
        from_attributes = True


class SalesOrderListResponse(BaseModel):
    total: int
    items: List[SalesOrderResponse]


# ==================== 生产订单 Schema ====================


class ProductionOrderItemBase(BaseModel):
    material_id: UUID
    quantity: Decimal = Field(...)


class ProductionOrderItemCreate(ProductionOrderItemBase):
    pass


class ProductionOrderItemResponse(ProductionOrderItemBase):
    id: UUID
    consumed_quantity: Decimal
    material: MaterialResponse
    created_at: datetime

    class Config:
        from_attributes = True


class ProductionOrderImageResponse(BaseModel):
    id: UUID
    order_id: UUID
    image_type: str
    image_url: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class YieldUpdate(BaseModel):
    completed_quantity: Decimal = Field(..., ge=0)


class ProductionOrderBase(BaseModel):
    sales_order_id: Optional[UUID] = None
    product_id: UUID
    quantity: Decimal = Field(...)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    remark: Optional[str] = None


class ProductionOrderCreate(ProductionOrderBase):
    pass


class ProductionOrderUpdate(BaseModel):
    product_id: Optional[UUID] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProductionOrderStatusEnum] = None
    remark: Optional[str] = None


class ProductionOrderResponse(ProductionOrderBase):
    id: UUID
    order_no: str
    completed_quantity: Optional[Decimal] = None
    status: ProductionOrderStatusEnum
    created_at: datetime
    updated_at: datetime
    product: MaterialResponse
    sales_order: Optional[SalesOrderResponse] = None
    items: List[ProductionOrderItemResponse] = []
    images: List[ProductionOrderImageResponse] = []

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
    can_view_dashboard: bool = True
    can_manage_materials: bool = True
    can_manage_sales: bool = True
    can_manage_production: bool = True
    can_manage_inventory: bool = True
    can_manage_users: bool = False
    can_create_sales: bool = False
    can_create_production: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    can_view_dashboard: Optional[bool] = None
    can_manage_materials: Optional[bool] = None
    can_manage_sales: Optional[bool] = None
    can_manage_production: Optional[bool] = None
    can_manage_inventory: Optional[bool] = None
    can_manage_users: Optional[bool] = None
    can_create_sales: Optional[bool] = None
    can_create_production: Optional[bool] = None


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
    user: Optional[dict] = None


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
