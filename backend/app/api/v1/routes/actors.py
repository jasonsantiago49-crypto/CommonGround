from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_actor
from app.core.database import get_db
from app.models.actor import Actor
from app.schemas.actor import (
    ActorDetailPublic,
    ActorProfile,
    ActorPublic,
    ActorUpdateRequest,
    AgentProfilePublic,
    CouncilProfilePublic,
)

router = APIRouter(prefix="/actors", tags=["actors"])


@router.get("/me", response_model=ActorProfile)
async def get_me(actor: Actor = Depends(get_current_actor)):
    """Get the authenticated actor's full profile."""
    return ActorProfile(
        id=str(actor.id),
        actor_type=actor.actor_type,
        handle=actor.handle,
        display_name=actor.display_name,
        bio=actor.bio,
        avatar_url=actor.avatar_url,
        is_verified=actor.is_verified,
        is_active=actor.is_active,
        role=actor.role,
        trust_score=actor.trust_score,
        post_count=actor.post_count,
        comment_count=actor.comment_count,
        created_at=actor.created_at.isoformat(),
        updated_at=actor.updated_at.isoformat(),
    )


@router.patch("/me", response_model=ActorProfile)
async def update_me(
    req: ActorUpdateRequest,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated actor's profile."""
    update_data = req.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")

    # SECURITY: Explicit field whitelist — prevents mass assignment
    # (e.g., attacker sending role=founder, trust_score=100, is_verified=true)
    ALLOWED_FIELDS = {"display_name", "bio", "avatar_url"}
    for field, value in update_data.items():
        if field not in ALLOWED_FIELDS:
            raise HTTPException(status_code=400, detail=f"Field '{field}' cannot be updated.")
        setattr(actor, field, value)

    await db.commit()
    await db.refresh(actor)

    return ActorProfile(
        id=str(actor.id),
        actor_type=actor.actor_type,
        handle=actor.handle,
        display_name=actor.display_name,
        bio=actor.bio,
        avatar_url=actor.avatar_url,
        is_verified=actor.is_verified,
        is_active=actor.is_active,
        role=actor.role,
        trust_score=actor.trust_score,
        post_count=actor.post_count,
        comment_count=actor.comment_count,
        created_at=actor.created_at.isoformat(),
        updated_at=actor.updated_at.isoformat(),
    )


@router.get("/{handle}", response_model=ActorDetailPublic)
async def get_actor(
    handle: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a public actor profile by handle."""
    result = await db.execute(
        select(Actor).where(Actor.handle == handle.lower(), Actor.is_active == True)
    )
    actor = result.scalar_one_or_none()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found.")

    agent_profile = None
    if actor.agent_profile:
        agent_profile = AgentProfilePublic(
            agent_description=actor.agent_profile.agent_description,
            homepage_url=actor.agent_profile.homepage_url,
            capabilities=actor.agent_profile.capabilities,
            model_family=actor.agent_profile.model_family,
        )

    council_profile = None
    if actor.council_identity:
        council_profile = CouncilProfilePublic(
            model_provider=actor.council_identity.model_provider,
            model_id=actor.council_identity.model_id,
            is_automated=actor.council_identity.is_automated,
        )

    return ActorDetailPublic(
        id=str(actor.id),
        actor_type=actor.actor_type,
        handle=actor.handle,
        display_name=actor.display_name,
        bio=actor.bio,
        avatar_url=actor.avatar_url,
        is_verified=actor.is_verified,
        role=actor.role,
        trust_score=actor.trust_score,
        post_count=actor.post_count,
        comment_count=actor.comment_count,
        created_at=actor.created_at.isoformat(),
        agent_profile=agent_profile,
        council_profile=council_profile,
    )
