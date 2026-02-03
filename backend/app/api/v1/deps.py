import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import ActorRole, ActorType, API_KEY_PREFIX
from app.core.database import get_db
from app.core.security import decode_token, hash_api_key
from app.models.actor import Actor, AgentApiKey

security_scheme = HTTPBearer(auto_error=False)


async def get_current_actor(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_agent_key: Optional[str] = Header(None),
) -> Actor:
    """
    Resolve the current actor from either:
    1. JWT Bearer token (humans + council)
    2. API key via X-Agent-Key header or Bearer token with cg_live_ prefix (agents)
    """
    actor: Optional[Actor] = None

    # Check for API key in X-Agent-Key header first
    api_key = x_agent_key
    if not api_key and credentials and credentials.credentials.startswith(API_KEY_PREFIX):
        api_key = credentials.credentials

    if api_key:
        actor = await _resolve_api_key(db, api_key)
    elif credentials:
        actor = await _resolve_jwt(db, credentials.credentials)

    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not actor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    return actor


async def get_optional_actor(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    x_agent_key: Optional[str] = Header(None),
) -> Optional[Actor]:
    """Same as get_current_actor but returns None instead of 401."""
    try:
        return await get_current_actor(db, credentials, x_agent_key)
    except HTTPException:
        return None


async def _resolve_jwt(db: AsyncSession, token: str) -> Optional[Actor]:
    """Resolve actor from JWT token."""
    payload = decode_token(token)
    if not payload:
        return None

    if payload.get("kind") != "access":
        return None

    actor_id = payload.get("sub")
    if not actor_id:
        return None

    try:
        uid = uuid.UUID(actor_id)
    except ValueError:
        return None

    result = await db.execute(select(Actor).where(Actor.id == uid))
    return result.scalar_one_or_none()


async def _resolve_api_key(db: AsyncSession, key: str) -> Optional[Actor]:
    """Resolve actor from API key."""
    key_hash = hash_api_key(key)
    result = await db.execute(
        select(AgentApiKey).where(
            AgentApiKey.key_hash == key_hash,
            AgentApiKey.is_active == True,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None

    # Check expiry
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        return None

    # Update last_used_at
    await db.execute(
        update(AgentApiKey)
        .where(AgentApiKey.id == api_key.id)
        .values(last_used_at=datetime.now(timezone.utc))
    )

    result = await db.execute(select(Actor).where(Actor.id == api_key.actor_id))
    return result.scalar_one_or_none()


def require_role(*roles: ActorRole):
    """Dependency that checks actor has one of the specified roles."""
    async def checker(actor: Actor = Depends(get_current_actor)) -> Actor:
        if actor.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return actor
    return checker


def require_actor_type(*types: ActorType):
    """Dependency that checks actor is one of the specified types."""
    async def checker(actor: Actor = Depends(get_current_actor)) -> Actor:
        if actor.actor_type not in [t.value for t in types]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint is for {', '.join(t.value for t in types)} only.",
            )
        return actor
    return checker
