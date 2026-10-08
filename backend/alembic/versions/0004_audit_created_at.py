"""Audit timestamps. Revision 0004."""
from alembic import op
import sqlalchemy as sa

revision = "0004_audit_created_at"
down_revision = "0003_markup_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("created_at", sa.DateTime, nullable=True))
    op.execute("UPDATE audit_log SET created_at = NOW() WHERE created_at IS NULL")


def downgrade() -> None:
    op.drop_column("audit_log", "created_at")
