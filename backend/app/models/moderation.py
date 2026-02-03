import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ModAction
from app.models.base import Base, TimestampMixin


class ModerationAction(TimestampMixin, Base):
    __tablename__ = "moderation_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    moderator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(16), nullable=False  # "post" or "comment"
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        Enum(ModAction, name="mod_action_enum", create_type=False,
             values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    duration_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flag_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("flags.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_reversed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    reversed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="SET NULL"),
        nullable=True,
    )
    reversed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    moderator = relationship("Actor", foreign_keys=[moderator_id], lazy="joined")
    reversed_by = relationship("Actor", foreign_keys=[reversed_by_id], lazy="joined")
    flag = relationship("Flag", lazy="joined")

    def __repr__(self) -> str:
        return f"<ModerationAction {self.id} {self.action} on {self.target_type}/{self.target_id}>"


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    actor = relationship("Actor", lazy="joined")

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} {self.action} on {self.resource_type}/{self.resource_id}>"
