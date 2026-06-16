from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, selectinload
from app.config import settings
from app.database import get_db
from app.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, plain_password)


def get_password_hash(password: str) -> str:
    return generate_password_hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = (
        db.query(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .filter(User.username == username)
        .first()
    )
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_roles(*role_codes: str):
    """[已废弃] 请使用 require_permissions
    要求用户至少拥有指定角色之一（admin 角色自动通过）"""

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role_codes = {ur.role_code for ur in current_user.roles}
        if "admin" in user_role_codes:
            return current_user
        if not user_role_codes.intersection(role_codes):
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user

    return role_checker


def require_permissions(*permissions: str):
    """基于 Boolean 权限标签检查（超级管理员自动通过）

    permissions 对应 User 模型的 Boolean 字段：
    can_manage_production / can_create_production / can_manage_sales / can_create_sales
    can_manage_materials / can_manage_users / is_superuser
    """

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        for perm in permissions:
            if getattr(current_user, perm, False):
                return current_user
        raise HTTPException(status_code=403, detail="权限不足")
        return current_user  # unreachable

    return permission_checker