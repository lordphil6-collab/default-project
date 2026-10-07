"""Markup rules table (model shipped in Phase 6 without a migration). Revision 0003."""
from alembic import op
import sqlalchemy as sa

revision = "0003_markup_rules"
down_revision = "0002_agents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "markup_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False, server_default="Standard"),
        sa.Column("kind", sa.String(32), nullable=False, server_default="percent"),
        sa.Column("value", sa.Float, nullable=False, server_default="0"),
        sa.Column("min_margin", sa.Float, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("markup_rules")
