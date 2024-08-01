"""schema_1.14.1

Revision ID: 4de7ec4f7f03
Revises: c5d04cc55476
Create Date: 2024-04-19 18:48:13.953125

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4de7ec4f7f03"
down_revision: Union[str, None] = "c5d04cc55476"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "protein_consequence",
        sa.Column("protein_consequence_id", sa.Integer(), nullable=False),
        sa.Column(
            "posedit_aa1",
            sa.String(),
            nullable=False,
            comment="The Posedit string using the 1 letter amino acid code.",
        ),
        sa.Column(
            "posedit_aa3",
            sa.String(),
            nullable=False,
            comment="The Posedit string using the 3 letter amino acid code.",
        ),
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
        sa.ForeignKeyConstraint(
            ["protein_consequence_id"],
            ["sequence_variant.sequence_variant_id"],
            name=op.f(
                "fk_protein_consequence_protein_consequence_id_sequence_variant"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "protein_consequence_id", name=op.f("pk_protein_consequence")
        ),
        comment="For search purposes, store the protein consequence in both 1 letter and 3 letter amino acid codes. Not normalized. Use this in Algolia or other search engines in addition to the normalized hgvs string.",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.execute(
        """
            DROP MATERIALIZED VIEW IF EXISTS variant_num_individuals_mv CASCADE;
        """
    )

    op.execute(
        """
            DROP VIEW IF EXISTS variant_to_exon_v CASCADE;
            """
    )

    op.execute(
        """
        DROP VIEW IF EXISTS p_variant_to_structure_v CASCADE;
        """
    )

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("protein_consequence")
    # ### end Alembic commands ###
