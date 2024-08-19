from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .individual import Individual


class Treatment(Base):
    __tablename__ = "treatment"

    treatment_id: Mapped[int] = mapped_column(primary_key=True)
    treatment_name: Mapped[str] = mapped_column(CITEXT, unique=True)

    individuals: Mapped[Optional[list["TreatmentRecord"]]] = relationship(
        "TreatmentRecord",
        back_populates="treatment",
    )

    __table_args__ = (
        {
            "comment": "Treatments that patients were given",
        },
    )


class TreatmentRecord(Base):
    __tablename__ = "treatment_record"

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("individual.individual_id"), primary_key=True
    )
    treatment_id: Mapped[int] = mapped_column(
        ForeignKey("treatment.treatment_id"), primary_key=True, index=True
    )
    treatment_taken: Mapped[bool] = mapped_column(comment="Was the treatment taken?")
    effective: Mapped[bool | None] = mapped_column(
        comment="Was the treatment effective?"
    )

    individual: Mapped["Individual"] = relationship(
        "Individual",
        back_populates="treatments",
    )
    treatment: Mapped["Treatment"] = relationship(
        "Treatment",
        back_populates="individuals",
    )

    __table_args__ = (
        {
            "comment": "Records of treatments that individuals were given",
        },
    )


__all__ = [
    "Treatment",
    "TreatmentRecord",
]
