import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Vote(TimestampMixin, Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("actor_id", "target_type", "target_id", name="uq_vote_per_target"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
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
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 or -1
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
