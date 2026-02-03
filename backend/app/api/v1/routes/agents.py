import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_actor, require_actor_type
from app.core.constants import ActorType
from app.core.database import get_db
from app.models.actor import Actor, AgentApiKey
from app.schemas.auth import (
    AgentRegisterRequest,
    AgentRegisterResponse,
    ApiKeyCreateRequest,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
)
from app.services.auth_service import (
    AuthError,
    create_api_key,
    register_agent,
    revoke_api_key,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/register", response_model=AgentRegisterResponse, status_code=201)
async def agent_register(
    req: AgentRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new AI agent. Returns the API key exactly once.
    Store it securely - it cannot be retrieved again.
    """
    try:
        return await register_agent(db, req)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(
    req: ApiKeyCreateRequest,
    actor: Actor = Depends(require_actor_type(ActorType.AGENT)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for the authenticated agent."""
    full_key, key_record = await create_api_key(db, actor.id, req.name)
    return ApiKeyCreatedResponse(
        id=str(key_record.id),
        name=key_record.name,
        key_prefix=key_record.key_prefix,
        is_active=key_record.is_active,
        created_at=key_record.created_at.isoformat(),
        api_key=full_key,
    )


@router.get("/keys", response_model=list[ApiKeyResponse])
async def list_keys(
    actor: Actor = Depends(require_actor_type(ActorType.AGENT)),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the authenticated agent."""
    result = await db.execute(
        select(AgentApiKey)
        .where(AgentApiKey.actor_id == actor.id)
        .order_by(AgentApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def delete_key(
    key_id: uuid.UUID,
    actor: Actor = Depends(require_actor_type(ActorType.AGENT)),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    success = await revoke_api_key(db, actor.id, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found.")
    return {"status": "ok", "detail": "API key revoked."}
