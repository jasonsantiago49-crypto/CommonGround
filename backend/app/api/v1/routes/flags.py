import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.api.v1.deps import get_current_actor, require_role
from app.core.config import settings
from app.core.constants import ActorRole, FlagStatus
from app.core.database import get_db

logger = structlog.get_logger()
from app.core.rate_limiter import rate_limit_flag
from app.models.actor import Actor
from app.models.comment import Comment
from app.models.flag import Flag
from app.models.moderation import AuditLog
from app.models.post import Post
from app.schemas.flag import FlagCreate, FlagPublic, FlagUpdate

router = APIRouter(prefix="/flags", tags=["flags"])


async def _enrich_flag(flag: Flag) -> FlagPublic:
    """Build FlagPublic from a Flag with reporter info."""
    reporter = flag.reporter
    return FlagPublic(
        id=str(flag.id),
        reporter_handle=reporter.handle if reporter else "unknown",
        reporter_type=reporter.actor_type if reporter else "unknown",
        target_type=flag.target_type,
        target_id=str(flag.target_id),
        reason=flag.reason,
        details=flag.details,
        status=flag.status,
        reviewed_at=flag.reviewed_at.isoformat() if flag.reviewed_at else None,
        created_at=flag.created_at.isoformat(),
    )


@router.post("", response_model=FlagPublic, status_code=201)
async def create_flag(
    req: FlagCreate,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit_flag),
):
    """Flag content for moderator review."""
    target_uuid = uuid.UUID(req.target_id)

    # Verify target exists and get author
    if req.target_type == "post":
        result = await db.execute(select(Post).where(Post.id == target_uuid))
        target = result.scalar_one_or_none()
    else:
        result = await db.execute(select(Comment).where(Comment.id == target_uuid))
        target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail=f"{req.target_type.title()} not found.")

    # Can't flag own content
    if target.author_id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot flag your own content.")

    # Check for duplicate flag
    result = await db.execute(
        select(Flag).where(
            Flag.reporter_id == actor.id,
            Flag.target_type == req.target_type,
            Flag.target_id == target_uuid,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You have already flagged this content.")

    flag = Flag(
        reporter_id=actor.id,
        target_type=req.target_type,
        target_id=target_uuid,
        reason=req.reason,
        details=req.details,
        status=FlagStatus.PENDING.value,
    )
    db.add(flag)

    # Audit log
    audit = AuditLog(
        actor_id=actor.id,
        action="flag_created",
        resource_type=req.target_type,
        resource_id=target_uuid,
        details={"reason": req.reason},
    )
    db.add(audit)

    await db.flush()

    # ── Auto-hide: count pending flags for this target ──────────────
    flag_count_result = await db.execute(
        select(sa_func.count(Flag.id)).where(
            Flag.target_type == req.target_type,
            Flag.target_id == target_uuid,
            Flag.status == FlagStatus.PENDING.value,
        )
    )
    flag_count = flag_count_result.scalar() or 0

    if flag_count >= settings.flag_threshold_hide and not target.is_removed:
        target.is_removed = True
        auto_action = "auto_hide"
        if flag_count >= settings.flag_threshold_remove:
            auto_action = "auto_remove"
        db.add(AuditLog(
            actor_id=actor.id,
            action=auto_action,
            resource_type=req.target_type,
            resource_id=target_uuid,
            details={
                "reason": f"Flag count ({flag_count}) reached threshold",
                "flag_count": flag_count,
                "threshold": settings.flag_threshold_hide,
            },
        ))
        logger.info(
            "auto_hide_triggered",
            target_type=req.target_type,
            target_id=str(target_uuid),
            flag_count=flag_count,
        )

    await db.commit()
    await db.refresh(flag)

    return await _enrich_flag(flag)


@router.get("/mine", response_model=list[FlagPublic])
async def my_flags(
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List flags I've submitted."""
    result = await db.execute(
        select(Flag)
        .where(Flag.reporter_id == actor.id)
        .order_by(Flag.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    flags = result.scalars().all()
    return [await _enrich_flag(f) for f in flags]


@router.get("/queue", response_model=list[FlagPublic])
async def flag_queue(
    actor: Actor = Depends(require_role(ActorRole.MODERATOR, ActorRole.ADMIN, ActorRole.FOUNDER)),
    db: AsyncSession = Depends(get_db),
    status: str = Query("pending", pattern="^(pending|reviewed|actioned|dismissed)$"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List flags for moderator review."""
    result = await db.execute(
        select(Flag)
        .where(Flag.status == status)
        .order_by(Flag.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    flags = result.scalars().all()
    return [await _enrich_flag(f) for f in flags]


@router.patch("/{flag_id}", response_model=FlagPublic)
async def update_flag(
    flag_id: uuid.UUID,
    req: FlagUpdate,
    actor: Actor = Depends(require_role(ActorRole.MODERATOR, ActorRole.ADMIN, ActorRole.FOUNDER)),
    db: AsyncSession = Depends(get_db),
):
    """Update flag status (moderator action)."""
    result = await db.execute(select(Flag).where(Flag.id == flag_id))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found.")

    flag.status = req.status
    flag.reviewer_id = actor.id
    flag.reviewed_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        actor_id=actor.id,
        action=f"flag_{req.status}",
        resource_type="flag",
        resource_id=flag.id,
        details={"target_type": flag.target_type, "target_id": str(flag.target_id)},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(flag)

    return await _enrich_flag(flag)
