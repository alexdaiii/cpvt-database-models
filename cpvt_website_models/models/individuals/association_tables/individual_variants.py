from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:
    from cpvt_website_models.models.variants.variant import Variant
    from cpvt_website_models.models.individuals.individual import Individual
    from .individual_variant_condition_link import \
        IndividualVariantConditionLink


class VariantInheritance(Base):
    __tablename__ = "variant_inheritance"

    variant_inheritance_id: Mapped[int] = mapped_column(primary_key=True)
    variant_inheritance: Mapped[CITEXT] = mapped_column(CITEXT, unique=True)

    individual_variants: Mapped[list["IndividualVariant"]] = relationship(
        "IndividualVariant",
        back_populates="variant_inheritance",
    )

    __table_args__ = {
        "comment": "Was the mutation was inherited or was spontaneous",
    }


class Zygosity(Base):
    __tablename__ = "zygosity"

    zygosity_id: Mapped[int] = mapped_column(primary_key=True)
    zygosity: Mapped[CITEXT] = mapped_column(CITEXT, unique=True)

    individual_variants: Mapped[list["IndividualVariant"]] = relationship(
        "IndividualVariant",
        back_populates="zygosity",
    )

    __table_args__ = {
        "comment": "Is the mutation on the individual heterozygous or "
                   "homozygous",
    }


class IndividualVariant(Base):
    """
    Association table between individuals and variants
    """

    __tablename__ = "individual_variant"

    individual_id: Mapped[int] = mapped_column(
        ForeignKey("individual.individual_id"), primary_key=True
    )
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variant.variant_id"), primary_key=True, index=True
    )
    variant_inheritance_id: Mapped[int | None] = mapped_column(
        ForeignKey("variant_inheritance.variant_inheritance_id"), index=True
    )
    zygosity_id: Mapped[int | None] = mapped_column(
        ForeignKey("zygosity.zygosity_id"), index=True
    )
    extra_information: Mapped[dict | None] = mapped_column(JSONB)

    # -- Relationships
    # Category of the mutation
    zygosity: Mapped["Zygosity"] = relationship(
        "Zygosity", back_populates="individual_variants"
    )
    variant_inheritance: Mapped["VariantInheritance"] = relationship(
        "VariantInheritance",
        back_populates="individual_variants",
    )

    # Links to Variant, and Individual
    variant: Mapped["Variant"] = relationship(
        "Variant", back_populates="individuals"
    )
    individual: Mapped["Individual"] = relationship(
        "Individual", back_populates="variants"
    )

    # Links patient_mutation to a patient_condition
    individual_variant_condition_links: Mapped[
        Optional[list["IndividualVariantConditionLink"]]
    ] = relationship(
        "IndividualVariantConditionLink",
        back_populates="individual_variant",
        overlaps="individual_condition,individual_variant_condition_links,individual_variant",
        # noqa: E501
    )

    __table_args__ = (
        {
            "comment": "A mutation that an individual has",
        },
    )


__all__ = [
    "VariantInheritance",
    "Zygosity",
    "IndividualVariant",
]
