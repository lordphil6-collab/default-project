"""Link quotations to agents. Revision 0007."""
from alembic import op
import sqlalchemy as sa

revision = "0007_quotation_agent_link"
down_revision = "0006_mail"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_quotations", sa.Column("agent_id", sa.String(36), nullable=True))
    op.create_foreign_key("fk_quotations_agent", "agent_quotations", "agents",
                          ["agent_id"], ["id"])
    # Best-effort backfill: exact company-name matches within the same org.
    op.execute("""
        UPDATE agent_quotations q SET agent_id = a.id
        FROM agents a
        WHERE q.agent_id IS NULL AND q.org_id = a.org_id AND lower(q.agent) = lower(a.company)
    """)


def downgrade() -> None:
    op.drop_constraint("fk_quotations_agent", "agent_quotations", type_="foreignkey")
    op.drop_column("agent_quotations", "agent_id")
