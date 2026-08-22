from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.schemas import Token
from app.models import User
from app.utils.auth import verify_password, create_access_token, get_current_active_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """登录获取Token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "can_manage_materials": user.can_manage_materials,
            "can_manage_sales": user.can_manage_sales,
            "can_manage_production": user.can_manage_production,
            "can_create_sales": user.can_create_sales,
            "can_create_production": user.can_create_production,
        }
    }


@router.get("/me/roles")
def get_my_roles(
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户的角色列表"""
    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "roles": [
            {"code": ur.role_code, "name": ur.role.name if ur.role else ur.role_code}
            for ur in current_user.roles
        ],
    }