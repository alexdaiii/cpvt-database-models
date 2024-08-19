from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from cpvt_website_models.models.publication import Publication
    from .association_tables import IndividualCondition, IndividualVariant
    from .treatments import TreatmentRecord
    from .family_history import FamilyHistoryRecord


class IndividualSex(Base):
    __tablename__ = "individual_sex"

    individual_sex_id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(CITEXT, unique=True)

    individuals: Mapped[list["Individual"]] = relationship("Individual")

    __table_args__ = ()


class Individual(Base):
    __tablename__ = "individual"

    individual_id: Mapped[int] = mapped_column(primary_key=True)
    individual_sex_id: Mapped[int | None] = mapped_column(
        ForeignKey("individual_sex.individual_sex_id"),
        index=True,
    )
    extra_information: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    conditions: Mapped[list["IndividualCondition"]] = relationship(
        "IndividualCondition",
        back_populates="individual",
    )
    variants: Mapped[list["IndividualVariant"]] = relationship(
        "IndividualVariant",
        back_populates="individual",
    )

    family_history_records: Mapped[list["FamilyHistoryRecord"]] = relationship(
        "FamilyHistoryRecord",
        back_populates="individual",
    )
    treatments: Mapped[list["TreatmentRecord"]] = relationship(
        "TreatmentRecord",
        back_populates="individual",
    )
    publications: Mapped[list["IndividualToPublication"]] = relationship(
        "IndividualToPublication",
        back_populates="individual",
    )
    original_row: Mapped["IndividualOriginalExcelRow"] = relationship(
        "IndividualOriginalExcelRow",
        back_populates="individual",
    )

    __table_args__ = (
        {
            "comment": "Contains information about an individual",
        },
    )


class IndividualOriginalExcelRow(Base):
    __tablename__ = "individual_original_excel_row"

    individual_id: Mapped[int] = mapped_column(
        ForeignKey("individual.individual_id"), primary_key=True
    )
    original_row: Mapped[dict] = mapped_column(JSONB)

    individual: Mapped["Individual"] = relationship(
        "Individual",
        back_populates="original_row",
    )

    __table_args__ = (
        {
            "comment": "Contains the original row from the excel file",
        },
    )


class IndividualToPublication(Base):
    __tablename__ = "individual_to_publication"

    individual_id: Mapped[int] = mapped_column(
        ForeignKey("individual.individual_id"), primary_key=True
    )
    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publication.publication_id"), primary_key=True, index=True
    )

    individual: Mapped["Individual"] = relationship(
        "Individual", back_populates="publications"
    )
    publication: Mapped["Publication"] = relationship(
        "Publication", back_populates="individuals"
    )

    __table_args__ = (
        {"comment": "Many-to-many relationship between individual " "and publication"},
    )


__all__ = [
    "Individual",
    "IndividualSex",
    "IndividualToPublication",
    "IndividualOriginalExcelRow",
]
