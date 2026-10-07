"""Agent database + RFQ recipients. Revision 0002."""
from alembic import op
import sqlalchemy as sa

revision = "0002_agents"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("routes", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("services", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("capabilities", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("contact", sa.String(320), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="Active"),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
    )
    op.create_table(
        "rfq_recipients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("rfq_id", sa.String(36), sa.ForeignKey("rfqs.id"), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="Selected"),
    )


def downgrade() -> None:
    op.drop_table("rfq_recipients")
    op.drop_table("agents")
