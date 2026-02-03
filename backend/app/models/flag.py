import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import FlagReason, FlagStatus
from app.models.base import Base, TimestampMixin


class Flag(TimestampMixin, Base):
    __tablename__ = "flags"
    __table_args__ = (
        UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_flag_per_target"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(16), nullable=False  # "post" or "comment"
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(
        Enum(FlagReason, name="flag_reason_enum", create_type=False,
             values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(FlagStatus, name="flag_status_enum", create_type=False,
             values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=FlagStatus.PENDING.value,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    reporter = relationship("Actor", foreign_keys=[reporter_id], lazy="joined")
    reviewer = relationship("Actor", foreign_keys=[reviewer_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<Flag {self.id} {self.reason} on {self.target_type}/{self.target_id}>"
