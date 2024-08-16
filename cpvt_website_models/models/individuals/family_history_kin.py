"""
Individual Kin's family history record
"""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:
    from .family_history import FamilyHistoryRecord


class KinshipName(Base):
    __tablename__ = "kinship_name"

    kinship_name_id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    name: Mapped[CITEXT] = mapped_column(
        CITEXT, unique=True, comment="Biological kinship name"
    )

    family_member_history: Mapped[list["FamilyMemberHistory"]] = relationship(
        "FamilyMemberHistory", back_populates="recorded_kin"
    )


class FamilyMemberHistory(Base):
    __tablename__ = "family_member_history"

    family_history_record_id: Mapped[int] = mapped_column(
        ForeignKey("family_history_record.family_history_record_id"),
        primary_key=True,
    )
    kinship_name_id: Mapped[int] = mapped_column(
        ForeignKey("kinship_name.kinship_name_id"),
        primary_key=True,
        index=True,
    )
    has_condition: Mapped[bool] = mapped_column(
        comment="Does this family member have the condition?"
    )

    family_history_record: Mapped["FamilyHistoryRecord"] = relationship(
        "FamilyHistoryRecord",
        back_populates="recorded_kin",
    )
    recorded_kin: Mapped["KinshipName"] = relationship(
        "KinshipName",
        back_populates="family_member_history",
    )


__all__ = [
    "KinshipName",
    "FamilyMemberHistory",
]
