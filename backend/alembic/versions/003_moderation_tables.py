"""Moderation tables - flags, moderation_actions, audit_log

Revision ID: 003
Revises: 002
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums (IF NOT EXISTS for safety)
    op.execute("DO $$ BEGIN CREATE TYPE flag_reason_enum AS ENUM ('spam', 'harassment', 'misinformation', 'impersonation', 'crypto', 'violence', 'other'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE flag_status_enum AS ENUM ('pending', 'reviewed', 'actioned', 'dismissed'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE mod_action_enum AS ENUM ('remove', 'restore', 'warn', 'mute', 'ban', 'pin', 'unpin', 'lock', 'unlock'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # flags
    op.create_table(
        "flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("reason", postgresql.ENUM("spam", "harassment", "misinformation", "impersonation", "crypto", "violence", "other", name="flag_reason_enum", create_type=False), nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("status", postgresql.ENUM("pending", "reviewed", "actioned", "dismissed", name="flag_status_enum", create_type=False), server_default=sa.text("'pending'"), nullable=False, index=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("reporter_id", "target_type", "target_id", name="uq_flag_per_target"),
    )
    op.create_index("idx_flags_target", "flags", ["target_type", "target_id"])

    # moderation_actions
    op.create_table(
        "moderation_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("moderator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("action", postgresql.ENUM("remove", "restore", "warn", "mute", "ban", "pin", "unpin", "lock", "unlock", name="mod_action_enum", create_type=False), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("duration_hours", sa.Integer, nullable=True),
        sa.Column("flag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("flags.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_reversed", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("reversed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_mod_actions_target", "moderation_actions", ["target_type", "target_id"])

    # audit_log
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_resource", "audit_log", ["resource_type", "resource_id"])
    op.create_index("idx_audit_created", "audit_log", [sa.text("created_at DESC")])

    # Updated_at triggers for flags and moderation_actions
    for table in ["flags", "moderation_actions"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    for table in ["moderation_actions", "flags"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    op.drop_table("audit_log")
    op.drop_table("moderation_actions")
    op.drop_table("flags")

    op.execute("DROP TYPE IF EXISTS mod_action_enum")
    op.execute("DROP TYPE IF EXISTS flag_status_enum")
    op.execute("DROP TYPE IF EXISTS flag_reason_enum")
