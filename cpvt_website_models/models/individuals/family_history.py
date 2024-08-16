from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:
    from cpvt_website_models.models.conditions import Condition
    from cpvt_website_models.models.individuals.individual import Individual
    from .family_history_kin import \
        FamilyMemberHistory


class FamilyHistoryRecord(Base):
    __tablename__ = "family_history_record"

    family_history_record_id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    individual_id: Mapped[int] = mapped_column(
        ForeignKey("individual.individual_id")
    )
    condition_id: Mapped[int] = mapped_column(
        ForeignKey("condition.condition_id"), index=True
    )
    num_family_members: Mapped[int | None] = mapped_column(
        comment="The number of family members with the condition. "
                "If this number is 0, then no family members have "
                "the condition. Recorded as number if the actual kinship is not known."
    )

    # Relationships
    # Tables this association table is associated with
    individual: Mapped["Individual"] = relationship(
        "Individual",
        back_populates="family_history_records",
    )
    condition: Mapped["Condition"] = relationship(
        "Condition",
        back_populates="family_history_records",
    )
    recorded_kin: Mapped[list["FamilyMemberHistory"]] = relationship(
        "FamilyMemberHistory",
        back_populates="family_history_record",
    )

    __table_args__ = (
        UniqueConstraint(
            "individual_id",
            "condition_id",
        ),
        CheckConstraint("num_family_members >= 0", "num_members_gte_0"),
    )


__all__ = [
    "FamilyHistoryRecord",
]
