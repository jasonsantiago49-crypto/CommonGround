"""Initial schema - actors, profiles, API keys, council identities

Revision ID: 001
Revises: None
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Enums
    actor_type_enum = postgresql.ENUM(
        "human", "agent", "council", name="actor_type_enum", create_type=False
    )
    actor_role_enum = postgresql.ENUM(
        "member", "moderator", "admin", "founder", name="actor_role_enum", create_type=False
    )
    op.execute("CREATE TYPE actor_type_enum AS ENUM ('human', 'agent', 'council')")
    op.execute("CREATE TYPE actor_role_enum AS ENUM ('member', 'moderator', 'admin', 'founder')")

    # actors
    op.create_table(
        "actors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("actor_type", actor_type_enum, nullable=False),
        sa.Column("handle", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(64), nullable=False),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("role", actor_role_enum, server_default=sa.text("'member'"), nullable=False),
        sa.Column("trust_score", sa.Float, server_default=sa.text("1.0"), nullable=False),
        sa.Column("post_count", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("comment_count", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # human_profiles
    op.create_table(
        "human_profiles",
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # agent_profiles
    op.create_table(
        "agent_profiles",
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("agent_description", sa.Text, nullable=True),
        sa.Column("homepage_url", sa.String(512), nullable=True),
        sa.Column("capabilities", postgresql.JSONB, nullable=True),
        sa.Column("model_family", sa.String(64), nullable=True),
        sa.Column("operator_contact", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # agent_api_keys
    op.create_table(
        "agent_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("name", sa.String(64), server_default=sa.text("'default'"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # council_identities
    op.create_table(
        "council_identities",
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("model_provider", sa.String(32), nullable=False),
        sa.Column("model_id", sa.String(64), nullable=False),
        sa.Column("is_automated", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("last_post_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Trigger for updated_at auto-update
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    for table in ["actors", "human_profiles", "agent_profiles", "agent_api_keys", "council_identities"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    for table in ["council_identities", "agent_api_keys", "agent_profiles", "human_profiles", "actors"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    op.drop_table("council_identities")
    op.drop_table("agent_api_keys")
    op.drop_table("agent_profiles")
    op.drop_table("human_profiles")
    op.drop_table("actors")

    op.execute("DROP TYPE IF EXISTS actor_role_enum")
    op.execute("DROP TYPE IF EXISTS actor_type_enum")
