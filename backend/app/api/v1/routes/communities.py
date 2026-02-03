import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_actor, get_optional_actor, require_role
from app.core.constants import ActorRole
from app.core.database import get_db
from app.models.actor import Actor
from app.models.community import Community, CommunityMembership
from app.schemas.community import CommunityCreate, CommunityPublic, CommunityUpdate

router = APIRouter(prefix="/communities", tags=["communities"])


@router.get("", response_model=list[CommunityPublic])
async def list_communities(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all communities."""
    result = await db.execute(
        select(Community)
        .order_by(Community.member_count.desc())
        .offset(offset)
        .limit(limit)
    )
    communities = result.scalars().all()
    return [
        CommunityPublic(
            id=str(c.id),
            slug=c.slug,
            name=c.name,
            description=c.description,
            rules=c.rules,
            is_default=c.is_default,
            member_count=c.member_count,
            post_count=c.post_count,
            created_at=c.created_at.isoformat(),
        )
        for c in communities
    ]


@router.get("/{slug}", response_model=CommunityPublic)
async def get_community(slug: str, db: AsyncSession = Depends(get_db)):
    """Get a community by slug."""
    result = await db.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found.")
    return CommunityPublic(
        id=str(community.id),
        slug=community.slug,
        name=community.name,
        description=community.description,
        rules=community.rules,
        is_default=community.is_default,
        member_count=community.member_count,
        post_count=community.post_count,
        created_at=community.created_at.isoformat(),
    )


@router.post("", response_model=CommunityPublic, status_code=201)
async def create_community(
    req: CommunityCreate,
    actor: Actor = Depends(require_role(ActorRole.ADMIN, ActorRole.FOUNDER)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new community (admin/founder only)."""
    existing = await db.execute(
        select(Community).where(Community.slug == req.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Community slug already exists.")

    community = Community(
        slug=req.slug,
        name=req.name,
        description=req.description,
        rules=req.rules,
        is_default=req.is_default,
    )
    db.add(community)
    await db.commit()
    await db.refresh(community)

    return CommunityPublic(
        id=str(community.id),
        slug=community.slug,
        name=community.name,
        description=community.description,
        rules=community.rules,
        is_default=community.is_default,
        member_count=community.member_count,
        post_count=community.post_count,
        created_at=community.created_at.isoformat(),
    )


@router.post("/{slug}/join")
async def join_community(
    slug: str,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Join a community."""
    result = await db.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found.")

    # Check if already a member
    existing = await db.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.actor_id == actor.id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "ok", "detail": "Already a member."}

    membership = CommunityMembership(
        community_id=community.id,
        actor_id=actor.id,
    )
    db.add(membership)
    community.member_count += 1
    await db.commit()
    return {"status": "ok", "detail": "Joined community."}


@router.post("/{slug}/leave")
async def leave_community(
    slug: str,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Leave a community."""
    result = await db.execute(select(Community).where(Community.slug == slug))
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found.")

    result = await db.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.actor_id == actor.id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        return {"status": "ok", "detail": "Not a member."}

    await db.delete(membership)
    community.member_count = max(0, community.member_count - 1)
    await db.commit()
    return {"status": "ok", "detail": "Left community."}
