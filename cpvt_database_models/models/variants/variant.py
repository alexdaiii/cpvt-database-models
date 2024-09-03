from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_database_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from cpvt_database_models.models.individuals import IndividualVariant
    from .variant_properties import ClinicalSignificance, VariantClinVarInfo
    from .variant_origins import DatasetVariant, PublicationVariant
    from .variant_links import ClinVarVariantLinkedCondition
    from .hgvs_variant import SequenceVariantDb


class Variant(Base):
    __tablename__ = "variant"

    variant_id: Mapped[int] = mapped_column(primary_key=True)
    hgvs_string: Mapped[str] = mapped_column(
        unique=True, comment="HGVS string. Can use any reference sequence."
    )
    hgvs_string_definitely_invalid: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="Whether the HGVS string is NOT parsable. "
        "A parsable HGVS string is one that can be made into a "
        "SequenceVariant (in the sequence_variant table). If this is true, "
        "then the string is invalid and not parsable.",
    )

    clinical_significance_id: Mapped[int | None] = mapped_column(
        ForeignKey("clinical_significance.clinical_significance_id"),
        index=True,
    )
    sequence_variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("sequence_variant.sequence_variant_id"),
        index=True,
    )

    extra_information: Mapped[dict | None] = mapped_column(JSONB)

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------
    # 1 - 0 links (optional properties)
    # -----
    clinvar_info: Mapped[Optional["VariantClinVarInfo"]] = relationship(
        "VariantClinVarInfo",
        back_populates="variant",
    )

    # N - 0 links
    # -----
    sequence_variant: Mapped[Optional["SequenceVariantDb"]] = relationship(
        "SequenceVariantDb",
        back_populates="variant",
    )
    clinical_significance: Mapped[Optional["ClinicalSignificance"]] = relationship(
        "ClinicalSignificance",
        back_populates="variants",
    )

    # M - N association tables
    # -----
    # Origins
    datasets: Mapped[list["DatasetVariant"]] = relationship(
        "DatasetVariant",
        back_populates="variant",
    )
    publications: Mapped[list["PublicationVariant"]] = relationship(
        "PublicationVariant",
        back_populates="variant",
    )

    # No category
    clinvar_linked_conditions: Mapped[list["ClinVarVariantLinkedCondition"]] = (
        relationship(
            "ClinVarVariantLinkedCondition",
            back_populates="variant",
        )
    )

    # Individual
    individuals: Mapped[list["IndividualVariant"]] = relationship(
        "IndividualVariant",
        back_populates="variant",
    )

    __table_args__ = ()


__all__ = [
    "Variant",
]
