import structlog
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limiter import rate_limit_login, rate_limit_register
from app.schemas.auth import (
    HumanRegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth_service import AuthError, login_human, register_human
from app.core.security import decode_token, create_access_token
from app.models.actor import Actor
from sqlalchemy import select

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    req: HumanRegisterRequest,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit_register),
):
    """Register a new human account."""
    try:
        return await register_human(db, req)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit_login),
):
    """Login with email and password. Returns access token + sets refresh cookie."""
    try:
        token_response, refresh_token = await login_human(db, req.email, req.password)
    except AuthError as e:
        logger.warning("login_failed", detail=e.detail)
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="cg_refresh",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 24 * 60 * 60,  # 30 days
        path="/api/v1/auth",
    )
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh an access token using a refresh token."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("kind") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    actor_id = payload.get("sub")
    if not actor_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    import uuid
    try:
        uid = uuid.UUID(actor_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    result = await db.execute(select(Actor).where(Actor.id == uid))
    actor = result.scalar_one_or_none()

    if not actor or not actor.is_active:
        raise HTTPException(status_code=401, detail="Account not found or deactivated.")

    access_token = create_access_token(
        subject=str(actor.id), actor_type=actor.actor_type
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=1800,
        actor_id=str(actor.id),
        handle=actor.handle,
        actor_type=actor.actor_type,
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear refresh token cookie."""
    response.delete_cookie(
        key="cg_refresh",
        path="/api/v1/auth",
    )
    return {"status": "ok"}
