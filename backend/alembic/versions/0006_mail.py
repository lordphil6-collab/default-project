"""Agent emails + mailbox configs. Revision 0006."""
from alembic import op
import sqlalchemy as sa

revision = "0006_mail"
down_revision = "0005_public_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("email", sa.String(320), nullable=False, server_default=""))
    op.create_table(
        "mailboxes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, server_default="imap"),
        sa.Column("host", sa.String(200), nullable=False, server_default=""),
        sa.Column("username", sa.String(320), nullable=False, server_default=""),
        sa.Column("secret", sa.Text, nullable=False, server_default=""),
        sa.Column("last_uid", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="Active"),
    )


def downgrade() -> None:
    op.drop_table("mailboxes")
    op.drop_column("agents", "email")
