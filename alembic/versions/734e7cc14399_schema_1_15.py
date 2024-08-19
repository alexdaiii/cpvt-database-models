"""schema_0.1.15

Revision ID: 734e7cc14399
Revises: 4de7ec4f7f03
Create Date: 2024-04-29 20:41:34.625254

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "734e7cc14399"
down_revision: Union[str, None] = "4de7ec4f7f03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "kv_store",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_kv_store")),
        comment="Key-Value store for storing arbitrary data and caching API responses without needing to spin up Redis",
    )
    op.create_index(
        "ix_kv_store_updated_at",
        "kv_store",
        ["updated_at"],
        unique=False,
        postgresql_using="brin",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_index(
    #     "ix_updated_at", table_name="kv_store", postgresql_using="brin"
    # )
    op.drop_table("kv_store")
    # ### end Alembic commands ###
