"""Mailbox provider ports (Gmail/Outlook/custom webmail). Revision 0008."""
from alembic import op
import sqlalchemy as sa

revision = "0008_mailbox_port"
down_revision = "0007_quotation_agent_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mailboxes", sa.Column("port", sa.Integer, nullable=False, server_default="993"))
    op.add_column("mailboxes", sa.Column("use_ssl", sa.Boolean, nullable=False, server_default="true"))


def downgrade() -> None:
    op.drop_column("mailboxes", "use_ssl")
    op.drop_column("mailboxes", "port")
