import hashlib
import secrets
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SystemToken, User
from app.schemas import (
    SystemTokenCreate,
    SystemTokenCreatedResponse,
    SystemTokenResponse,
    SystemTokenUpdate,
)
from app.utils.auth import get_current_session_user


router = APIRouter(prefix="/system-tokens", tags=["系统 Token 管理"])


def _require_superuser(current_user: User) -> None:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有超级管理员才能管理系统 Token")


def _as_utc_naive(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


@router.get("", response_model=List[SystemTokenResponse])
def list_system_tokens(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_session_user),
):
    _require_superuser(current_user)
    return db.query(SystemToken).order_by(SystemToken.created_at.desc()).all()


@router.get("/{token_id}", response_model=SystemTokenResponse)
def get_system_token(
    token_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_session_user),
):
    _require_superuser(current_user)
    token = db.query(SystemToken).filter(SystemToken.id == token_id).first()
    if token is None:
        raise HTTPException(status_code=404, detail="系统 Token 不存在")
    return token


@router.post("", response_model=SystemTokenCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_system_token(
    data: SystemTokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_session_user),
):
    _require_superuser(current_user)
    expires_at = _as_utc_naive(data.expires_at)
    if expires_at is not None and expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="过期时间必须晚于当前时间")

    plain_token = f"pdb_{secrets.token_urlsafe(32)}"
    token = SystemToken(
        name=data.name,
        description=data.description,
        token_hash=hashlib.sha256(plain_token.encode("utf-8")).hexdigest(),
        token_prefix=plain_token[:12],
        expires_at=expires_at,
        created_by=current_user.id,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    response = SystemTokenResponse.model_validate(token).model_dump()
    response["token"] = plain_token
    return response


@router.put("/{token_id}", response_model=SystemTokenResponse)
def update_system_token(
    token_id: UUID,
    data: SystemTokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_session_user),
):
    _require_superuser(current_user)
    token = db.query(SystemToken).filter(SystemToken.id == token_id).first()
    if token is None:
        raise HTTPException(status_code=404, detail="系统 Token 不存在")
    changes = data.model_dump(exclude_unset=True)
    if "expires_at" in changes:
        changes["expires_at"] = _as_utc_naive(changes["expires_at"])
    if changes.get("expires_at") is not None and changes["expires_at"] <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="过期时间必须晚于当前时间")
    for field, value in changes.items():
        setattr(token, field, value)
    db.commit()
    db.refresh(token)
    return token


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system_token(
    token_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_session_user),
):
    _require_superuser(current_user)
    token = db.query(SystemToken).filter(SystemToken.id == token_id).first()
    if token is None:
        raise HTTPException(status_code=404, detail="系统 Token 不存在")
    db.delete(token)
    db.commit()
