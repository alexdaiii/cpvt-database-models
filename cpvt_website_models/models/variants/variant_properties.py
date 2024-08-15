from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:
    from ..variants import Variant


# ---------------------------------------------------------
# 1-0 Properties (Optional Properties)
# ---------------------------------------------------------
class VariantClinVarInfo(Base):
    __tablename__ = "variant_clinvar_info"

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variant.variant_id"),
        primary_key=True,
    )
    variation_clinvar_id: Mapped[int] = mapped_column(
        unique=True,
        comment="Variation ID from ClinVar. "
                "Used to link to the ClinVar website",
    )

    variant: Mapped["Variant"] = relationship(
        "Variant",
        back_populates="clinvar_info",
    )

    __table_args__ = (
        {
            "comment": "Information about a variant if it is from ClinVar",
        },
    )


# ---------------------------------------------------------
# N-0 Properties (Categorical Properties)
# ---------------------------------------------------------
class ClinicalSignificance(Base):
    __tablename__ = "clinical_significance"

    clinical_significance_id: Mapped[int] = mapped_column(primary_key=True)
    clinical_significance: Mapped[CITEXT] = mapped_column(CITEXT, unique=True)

    variants: Mapped[list["Variant"]] = relationship(
        "Variant",
        back_populates="clinical_significance",
    )

    __table_args__ = (
        {
            "comment": "Clinical significance of a variant",
        },
    )


__all__ = [
    "VariantClinVarInfo",
    "ClinicalSignificance",
]
