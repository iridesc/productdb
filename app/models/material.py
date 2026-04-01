from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
    Enum,
    ForeignKey,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class MaterialCategoryEnum(str, enum.Enum):
    FINISHED_PRODUCT = "finished_product"  # 成品
    SEMI_FINISHED = "semi_finished"  # 半成品
    RAW_MATERIAL = "raw_material"  # 原材料
    AUXILIARY = "auxiliary"  # 辅料


class MaterialCategory(Base):
    __tablename__ = "material_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    parent_id = Column(
        UUID(as_uuid=True), ForeignKey("material_categories.id"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("MaterialCategory", remote_side=[id], backref="children")


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(Enum(MaterialCategoryEnum), nullable=False)
    unit = Column(String(20), default="个")
    specification = Column(String(200), nullable=True)
    safety_stock = Column(Numeric(10, 2), default=0)
    current_stock = Column(Numeric(10, 2), default=0)
    price = Column(Numeric(10, 2), default=0)
    sale_price = Column(Numeric(10, 2), default=0)
    other_cost = Column(Numeric(10, 2), default=0)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("material_categories.id"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category_info = relationship("MaterialCategory", backref="materials")
    bom_items = relationship(
        "BOM", back_populates="material", foreign_keys="BOM.material_id"
    )
    product_boms = relationship(
        "BOM", back_populates="product", foreign_keys="BOM.product_id"
    )
    images = relationship(
        "MaterialImage", back_populates="material", cascade="all, delete-orphan"
    )

    @property
    def thumbnail_url(self) -> str | None:
        if self.images:
            first_image = min(self.images, key=lambda x: x.sort_order)
            return first_image.image_url
        return None


class MaterialImage(Base):
    __tablename__ = "material_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(
        UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_url = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("Material", back_populates="images")
