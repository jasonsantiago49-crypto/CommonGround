import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_actor, require_role
from app.core.constants import (
    ActorRole, ModAction,
    TRUST_FLAG_ACTIONED, TRUST_WARNED, TRUST_MUTED, TRUST_MIN, TRUST_MAX,
)
from app.core.database import get_db
from app.models.actor import Actor
from app.models.comment import Comment
from app.models.moderation import AuditLog, ModerationAction
from app.models.post import Post
from app.schemas.moderation import AuditEntry, ModActionCreate, ModActionPublic

router = APIRouter(prefix="/moderation", tags=["moderation"])


async def _enrich_mod_action(action: ModerationAction) -> ModActionPublic:
    """Build ModActionPublic from a ModerationAction."""
    mod = action.moderator
    return ModActionPublic(
        id=str(action.id),
        moderator_handle=mod.handle if mod else "system",
        moderator_type=mod.actor_type if mod else "system",
        target_type=action.target_type,
        target_id=str(action.target_id),
        action=action.action,
        reason=action.reason,
        duration_hours=action.duration_hours,
        is_reversed=action.is_reversed,
        created_at=action.created_at.isoformat(),
    )


def _adjust_trust(actor: Actor, delta: float) -> None:
    """Clamp trust score within bounds."""
    actor.trust_score = max(TRUST_MIN, min(TRUST_MAX, actor.trust_score + delta))


@router.post("/actions", response_model=ModActionPublic, status_code=201)
async def take_action(
    req: ModActionCreate,
    actor: Actor = Depends(require_role(ActorRole.MODERATOR, ActorRole.ADMIN, ActorRole.FOUNDER)),
    db: AsyncSession = Depends(get_db),
):
    """Take a moderation action. Reason is required."""
    target_uuid = uuid.UUID(req.target_id)

    # Resolve target and its author
    target_author: Actor | None = None
    if req.target_type == "post":
        result = await db.execute(select(Post).where(Post.id == target_uuid))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="Post not found.")
        if target.author_id:
            result = await db.execute(select(Actor).where(Actor.id == target.author_id))
            target_author = result.scalar_one_or_none()
    else:
        result = await db.execute(select(Comment).where(Comment.id == target_uuid))
        target = result.scalar_one_or_none()
        if not target:
            raise HTTPException(status_code=404, detail="Comment not found.")
        if target.author_id:
            result = await db.execute(select(Actor).where(Actor.id == target.author_id))
            target_author = result.scalar_one_or_none()

    # Execute the action
    if req.action == ModAction.REMOVE.value:
        target.is_removed = True
        if target_author:
            _adjust_trust(target_author, TRUST_FLAG_ACTIONED)
    elif req.action == ModAction.RESTORE.value:
        target.is_removed = False
    elif req.action == ModAction.WARN.value:
        if target_author:
            _adjust_trust(target_author, TRUST_WARNED)
    elif req.action == ModAction.MUTE.value:
        if target_author:
            target_author.is_active = False
            _adjust_trust(target_author, TRUST_MUTED)
    elif req.action == ModAction.BAN.value:
        if target_author:
            target_author.is_active = False
            _adjust_trust(target_author, TRUST_MUTED)
    elif req.action == ModAction.PIN.value:
        if req.target_type == "post":
            target.is_pinned = True
    elif req.action == ModAction.UNPIN.value:
        if req.target_type == "post":
            target.is_pinned = False
    elif req.action == ModAction.LOCK.value:
        if req.target_type == "post":
            target.is_locked = True
    elif req.action == ModAction.UNLOCK.value:
        if req.target_type == "post":
            target.is_locked = False

    # Parse optional flag_id
    flag_uuid = uuid.UUID(req.flag_id) if req.flag_id else None

    # Create moderation action record
    mod_action = ModerationAction(
        moderator_id=actor.id,
        target_type=req.target_type,
        target_id=target_uuid,
        action=req.action,
        reason=req.reason,
        duration_hours=req.duration_hours,
        flag_id=flag_uuid,
    )
    db.add(mod_action)

    # Audit log
    audit = AuditLog(
        actor_id=actor.id,
        action=f"mod_{req.action}",
        resource_type=req.target_type,
        resource_id=target_uuid,
        details={
            "reason": req.reason,
            "target_author": target_author.handle if target_author else None,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(mod_action)

    return await _enrich_mod_action(mod_action)


@router.get("/log", response_model=list[ModActionPublic])
async def public_moderation_log(
    db: AsyncSession = Depends(get_db),
    target_type: str | None = Query(None, pattern="^(post|comment)$"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Public moderation log. No auth required.
    Anyone can view every moderation action ever taken.
    """
    query = select(ModerationAction).order_by(ModerationAction.created_at.desc())

    if target_type:
        query = query.where(ModerationAction.target_type == target_type)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    actions = result.scalars().all()
    return [await _enrich_mod_action(a) for a in actions]


@router.get("/log/{target_type}/{target_id}", response_model=list[ModActionPublic])
async def target_moderation_history(
    target_type: str,
    target_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public moderation history for a specific post or comment."""
    if target_type not in ("post", "comment"):
        raise HTTPException(status_code=400, detail="target_type must be 'post' or 'comment'.")

    result = await db.execute(
        select(ModerationAction)
        .where(
            ModerationAction.target_type == target_type,
            ModerationAction.target_id == target_id,
        )
        .order_by(ModerationAction.created_at.desc())
    )
    actions = result.scalars().all()
    return [await _enrich_mod_action(a) for a in actions]


@router.post("/actions/{action_id}/reverse", response_model=ModActionPublic)
async def reverse_action(
    action_id: uuid.UUID,
    actor: Actor = Depends(require_role(ActorRole.ADMIN, ActorRole.FOUNDER)),
    db: AsyncSession = Depends(get_db),
):
    """Reverse a moderation action (admin+ only)."""
    result = await db.execute(
        select(ModerationAction).where(ModerationAction.id == action_id)
    )
    mod_action = result.scalar_one_or_none()
    if not mod_action:
        raise HTTPException(status_code=404, detail="Moderation action not found.")

    if mod_action.is_reversed:
        raise HTTPException(status_code=400, detail="Action already reversed.")

    # Undo the effect
    if mod_action.target_type == "post":
        result = await db.execute(select(Post).where(Post.id == mod_action.target_id))
        target = result.scalar_one_or_none()
    else:
        result = await db.execute(select(Comment).where(Comment.id == mod_action.target_id))
        target = result.scalar_one_or_none()

    if target:
        if mod_action.action == ModAction.REMOVE.value:
            target.is_removed = False
        elif mod_action.action == ModAction.PIN.value:
            if hasattr(target, "is_pinned"):
                target.is_pinned = False
        elif mod_action.action == ModAction.LOCK.value:
            if hasattr(target, "is_locked"):
                target.is_locked = False

        # Reactivate author if was muted/banned
        if mod_action.action in (ModAction.MUTE.value, ModAction.BAN.value):
            if target.author_id:
                result = await db.execute(select(Actor).where(Actor.id == target.author_id))
                author = result.scalar_one_or_none()
                if author:
                    author.is_active = True

    mod_action.is_reversed = True
    mod_action.reversed_by_id = actor.id
    mod_action.reversed_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        actor_id=actor.id,
        action=f"mod_{mod_action.action}_reversed",
        resource_type=mod_action.target_type,
        resource_id=mod_action.target_id,
        details={"original_action_id": str(mod_action.id)},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(mod_action)

    return await _enrich_mod_action(mod_action)
