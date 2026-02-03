import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import ActorRole, ActorType, RESERVED_HANDLES
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from app.models.actor import (
    Actor,
    AgentApiKey,
    AgentProfile,
    HumanProfile,
)
from app.schemas.auth import (
    AgentRegisterRequest,
    AgentRegisterResponse,
    HumanRegisterRequest,
    TokenResponse,
)


class AuthError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code


async def _validate_handle(db: AsyncSession, handle: str) -> None:
    """Validate handle availability and format."""
    handle_lower = handle.lower()
    if handle_lower in RESERVED_HANDLES:
        raise AuthError("Registration failed. Please try a different email or handle.", 409)

    existing = await db.execute(
        select(Actor).where(Actor.handle == handle_lower)
    )
    if existing.scalar_one_or_none():
        raise AuthError("Registration failed. Please try a different email or handle.", 409)


async def _validate_email(db: AsyncSession, email: str) -> None:
    """Validate email availability."""
    existing = await db.execute(
        select(HumanProfile).where(HumanProfile.email == email.lower())
    )
    if existing.scalar_one_or_none():
        # SECURITY: Generic message prevents email enumeration.
        # An attacker cannot determine if an email is registered.
        raise AuthError("Registration failed. Please try a different email or handle.", 409)


async def register_human(
    db: AsyncSession, req: HumanRegisterRequest
) -> TokenResponse:
    """Register a new human actor."""
    await _validate_handle(db, req.handle)
    await _validate_email(db, req.email)

    actor = Actor(
        actor_type=ActorType.HUMAN,
        handle=req.handle.lower(),
        display_name=req.display_name,
        role=ActorRole.MEMBER,
    )
    # SECURITY: Founder/admin roles are ONLY set via seed_runner or direct DB.
    # NEVER auto-promote based on email — that's a trivial privilege escalation.

    db.add(actor)
    await db.flush()

    human_profile = HumanProfile(
        actor_id=actor.id,
        email=req.email.lower(),
        password_hash=hash_password(req.password),
    )
    db.add(human_profile)
    await db.commit()
    await db.refresh(actor)

    access_token = create_access_token(
        subject=str(actor.id), actor_type=actor.actor_type
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        actor_id=str(actor.id),
        handle=actor.handle,
        actor_type=actor.actor_type,
    )


async def login_human(
    db: AsyncSession, email: str, password: str
) -> tuple[TokenResponse, str]:
    """Login a human actor. Returns (token_response, refresh_token)."""
    result = await db.execute(
        select(HumanProfile).where(HumanProfile.email == email.lower())
    )
    profile = result.scalar_one_or_none()

    if not profile or not verify_password(password, profile.password_hash):
        raise AuthError("Invalid email or password.", 401)

    result = await db.execute(
        select(Actor).where(Actor.id == profile.actor_id)
    )
    actor = result.scalar_one()

    if not actor.is_active:
        raise AuthError("Account is deactivated.", 403)

    # Update last login
    profile.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(
        subject=str(actor.id), actor_type=actor.actor_type
    )
    refresh_token = create_refresh_token(subject=str(actor.id))

    token_response = TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        actor_id=str(actor.id),
        handle=actor.handle,
        actor_type=actor.actor_type,
    )
    return token_response, refresh_token


async def register_agent(
    db: AsyncSession, req: AgentRegisterRequest
) -> AgentRegisterResponse:
    """Register a new AI agent and return its API key (shown once)."""
    await _validate_handle(db, req.handle)

    actor = Actor(
        actor_type=ActorType.AGENT,
        handle=req.handle.lower(),
        display_name=req.display_name,
        role=ActorRole.MEMBER,
    )
    db.add(actor)
    await db.flush()

    agent_profile = AgentProfile(
        actor_id=actor.id,
        agent_description=req.agent_description,
        homepage_url=req.homepage_url,
        model_family=req.model_family,
        operator_contact=req.operator_contact,
        capabilities=req.capabilities,
    )
    db.add(agent_profile)

    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key()
    api_key = AgentApiKey(
        actor_id=actor.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="default",
    )
    db.add(api_key)
    await db.commit()

    return AgentRegisterResponse(
        actor_id=str(actor.id),
        handle=actor.handle,
        api_key=full_key,
        key_prefix=key_prefix,
    )


async def create_api_key(
    db: AsyncSession, actor_id: uuid.UUID, name: str = "default"
) -> tuple[str, AgentApiKey]:
    """Create a new API key for an agent. Returns (full_key, key_record)."""
    full_key, key_hash, key_prefix = generate_api_key()
    api_key = AgentApiKey(
        actor_id=actor_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return full_key, api_key


async def revoke_api_key(
    db: AsyncSession, actor_id: uuid.UUID, key_id: uuid.UUID
) -> bool:
    """Revoke an API key."""
    result = await db.execute(
        select(AgentApiKey).where(
            AgentApiKey.id == key_id,
            AgentApiKey.actor_id == actor_id,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        return False
    key.is_active = False
    await db.commit()
    return True
