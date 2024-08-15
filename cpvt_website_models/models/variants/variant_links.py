"""
Association tables for a mutation property or mutation to other table groups
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:
    from ..conditions import Condition
    from ..variants import Variant


class ClinVarVariantLinkedCondition(Base):
    __tablename__ = "clinvar_variant_linked_condition"

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variant.variant_id"), primary_key=True
    )
    condition_id: Mapped[int] = mapped_column(
        ForeignKey("condition.condition_id"), primary_key=True, index=True
    )

    variant: Mapped["Variant"] = relationship(
        "Variant", back_populates="clinvar_linked_conditions"
    )
    condition: Mapped["Condition"] = relationship(
        "Condition", back_populates="clinvar_linked_variants"
    )

    __table_args__ = (
        {
            "comment": "A record that ClinVar has linked a variant "
                       "to a condition",
        },
    )


__all__ = [
    "ClinVarVariantLinkedCondition",
]
