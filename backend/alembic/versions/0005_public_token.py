"""Public tracking token on situations. Revision 0005."""
from alembic import op
import sqlalchemy as sa

revision = "0005_public_token"
down_revision = "0004_audit_created_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("situations", sa.Column("public_token", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_situations_public_token", "situations", ["public_token"])


def downgrade() -> None:
    op.drop_constraint("uq_situations_public_token", "situations", type_="unique")
    op.drop_column("situations", "public_token")
