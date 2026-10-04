"""Initial schema — all Phase 2-7 tables. Revision 0001."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _org_fk():
    return sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("trial_start", sa.DateTime, nullable=False),
        sa.Column("trial_ends", sa.DateTime, nullable=True),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="CSR"),
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("contact", sa.String(320), nullable=False, server_default=""),
    )
    op.create_table(
        "situations",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("type", sa.String(64), nullable=False, server_default="import_quote"),
        sa.Column("status", sa.String(64), nullable=False, server_default="New"),
        sa.Column("shipment", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("missing", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("next_action", sa.String(500), nullable=False, server_default=""),
        sa.Column("outcome", sa.String(64), nullable=False, server_default=""),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("situation_id", sa.String(36), sa.ForeignKey("situations.id"), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False, server_default=""),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("attachments", sa.JSON, nullable=False, server_default="[]"),
    )
    op.create_table(
        "rfqs",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("situation_id", sa.String(36), sa.ForeignKey("situations.id"), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="Draft"),
        sa.Column("scope", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_table(
        "agent_quotations",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("rfq_id", sa.String(36), sa.ForeignKey("rfqs.id"), nullable=False),
        sa.Column("agent", sa.String(200), nullable=False, server_default=""),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("freight", sa.Float, nullable=False, server_default="0"),
        sa.Column("origin_charges", sa.Float, nullable=True),
        sa.Column("destination_charges", sa.Float, nullable=True),
        sa.Column("other_charges", sa.Float, nullable=False, server_default="0"),
        sa.Column("validity_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("transit_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("raw_text", sa.Text, nullable=False, server_default=""),
        sa.Column("selected", sa.Boolean, nullable=False, server_default="0"),
    )
    op.create_table(
        "customer_quotations",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("situation_id", sa.String(36), sa.ForeignKey("situations.id"), nullable=False),
        sa.Column("agent_quotation_id", sa.String(36), nullable=True),
        sa.Column("markup_rule_id", sa.String(36), nullable=True),
        sa.Column("agent_total", sa.Float, nullable=False, server_default="0"),
        sa.Column("markup_amount", sa.Float, nullable=False, server_default="0"),
        sa.Column("status", sa.String(64), nullable=False, server_default="Draft"),
        sa.Column("final_price", sa.Float, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("terms", sa.Text, nullable=False, server_default=""),
        sa.Column("validity_days", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("situation_id", sa.String(36), sa.ForeignKey("situations.id"), nullable=False),
        sa.Column("quote_id", sa.String(36), nullable=True),
        sa.Column("due_at", sa.DateTime, nullable=True),
        sa.Column("status", sa.String(64), nullable=False, server_default="Due"),
    )
    op.create_table(
        "exceptions",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("situation_id", sa.String(36), sa.ForeignKey("situations.id"), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text, nullable=False, server_default=""),
        sa.Column("owner", sa.String(320), nullable=False, server_default=""),
        sa.Column("next_action", sa.String(500), nullable=False, server_default=""),
        sa.Column("due_at", sa.DateTime, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="Open"),
    )
    op.create_table(
        "plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("monthly_price", sa.Float, nullable=False, server_default="0"),
    )
    op.create_table(
        "entitlements",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("status", sa.String(32), nullable=False, server_default="trialing"),
        sa.Column("plan_id", sa.String(36), nullable=True),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        _org_fk(),
        sa.Column("actor", sa.String(320), nullable=False, server_default=""),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("detail", sa.JSON, nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    for table in (
        "audit_log", "entitlements", "plans", "exceptions", "follow_ups",
        "customer_quotations", "agent_quotations", "rfqs", "messages",
        "conversations", "situations", "customers", "users", "organizations",
    ):
        op.drop_table(table)
