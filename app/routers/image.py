import os
import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import MaterialImage, Material, User
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/materials", tags=["物料图片"])

UPLOAD_DIR = "/app/uploads/images"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


class ImageResponse(BaseModel):
    id: UUID
    material_id: UUID
    image_url: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{material_id}/images", response_model=List[ImageResponse])
def get_material_images(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取物料图片列表"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物料不存在")

    images = (
        db.query(MaterialImage)
        .filter(MaterialImage.material_id == material_id)
        .order_by(MaterialImage.sort_order)
        .all()
    )
    return images


@router.post("/{material_id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    material_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """上传物料图片"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="物料不存在")

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
    
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(filepath, "wb") as f:
        f.write(content)

    max_sort = (
        db.query(MaterialImage.sort_order)
        .filter(MaterialImage.material_id == material_id)
        .order_by(MaterialImage.sort_order.desc())
        .first()
    )
    next_sort = (max_sort[0] + 1) if max_sort else 0

    image = MaterialImage(
        material_id=material_id,
        image_url=f"/api/v1/uploads/{unique_filename}",
        sort_order=next_sort,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return image


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除图片"""
    image = db.query(MaterialImage).filter(MaterialImage.id == image_id).first()
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


@router.put("/images/{image_id}/sort")
def update_image_sort(
    image_id: str,
    sort_order: int = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新图片排序"""
    image = db.query(MaterialImage).filter(MaterialImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图片不存在")

    image.sort_order = sort_order
    db.commit()
    db.refresh(image)

    return image
