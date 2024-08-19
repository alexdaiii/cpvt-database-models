from typing import TYPE_CHECKING

from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import Mapped, relationship, mapped_column

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .individual_variants import IndividualVariant
    from .individual_condition import IndividualCondition


class IndividualVariantConditionLink(Base):
    """
    Association table between an IndividualToVariant and an
    IndividualToCondition row
    """

    __tablename__ = "individual_variant_condition_link"

    individual_id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    variant_id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    condition_id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # -- Relationships
    individual_variant: Mapped["IndividualVariant"] = relationship(
        "IndividualVariant",
        back_populates="individual_variant_condition_links",
        overlaps="individual_condition",
    )
    individual_condition: Mapped["IndividualCondition"] = relationship(
        "IndividualCondition",
        back_populates="individual_variant_condition_links",
        overlaps="individual_variant",
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["individual_id", "variant_id"],
            [
                "individual_variant.individual_id",
                "individual_variant.variant_id",
            ],
            "fk_pmcl_individual_id_variant_id_individual_variant",
        ),
        ForeignKeyConstraint(
            ["individual_id", "condition_id"],
            [
                "individual_condition.individual_id",
                "individual_condition.condition_id",
            ],
            "fk_pmcl_individual_id_condition_id_individual_variant",
        ),
        {
            "comment": "A record that an individual has a variant that is "
                       "linked to one of their recorded conditions",
        },
    )


__all__ = [
    "IndividualVariantConditionLink",
]
