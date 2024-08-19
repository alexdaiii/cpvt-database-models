from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .individuals import FamilyHistoryRecord, IndividualCondition
    from .variants import ClinVarVariantLinkedCondition


class Condition(Base):
    __tablename__ = "condition"

    condition_id: Mapped[int] = mapped_column(
        primary_key=True, comment="Primary key for the health_state table"
    )
    condition: Mapped[str] = mapped_column(
        CITEXT,
        unique=True,
    )

    # -- Relationships
    synonyms: Mapped[Optional[list["ConditionSynonym"]]] = relationship(
        "ConditionSynonym",
        back_populates="condition",
    )

    # Association Tables
    individuals: Mapped[Optional[list["IndividualCondition"]]] = relationship(
        "IndividualCondition",
        back_populates="condition",
    )
    family_history_records: Mapped[
        Optional[list["FamilyHistoryRecord"]]
    ] = relationship(
        "FamilyHistoryRecord",
        back_populates="condition",
    )
    clinvar_linked_variants: Mapped[
        Optional[list["ClinVarVariantLinkedCondition"]]
    ] = relationship(
        "ClinVarVariantLinkedCondition",
        back_populates="condition",
    )

    __table_args__ = ()


class ConditionSynonym(Base):
    __tablename__ = "condition_synonym"

    condition_synonym_id: Mapped[int] = mapped_column(
        primary_key=True,
        comment="Primary key for the health_state_synonym table",
    )
    condition_id: Mapped[int] = mapped_column(
        ForeignKey(
            "condition.condition_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        comment="The condition that the synonym is for",
        index=True,
    )
    synonym: Mapped[str] = mapped_column(
        CITEXT,
    )

    condition: Mapped["Condition"] = relationship(
        "Condition", back_populates="synonyms"
    )

    __table_args__ = ()


__all__ = [
    "Condition",
    "ConditionSynonym",
]
