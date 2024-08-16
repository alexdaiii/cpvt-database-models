from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:
    from .individual_variant_condition_link import \
        IndividualVariantConditionLink
    from cpvt_website_models.models.individuals.individual import Individual
    from cpvt_website_models.models.conditions import Condition


class IndividualCondition(Base):
    """
    An association table between individuals and conditions that represents
    a record that an individual has reported having this condition or not
    """

    __tablename__ = "individual_condition"

    individual_id: Mapped[int] = mapped_column(
        ForeignKey("individual.individual_id"),
        comment="The individual who has a record of this condition",
        primary_key=True,
    )
    condition_id: Mapped[int] = mapped_column(
        ForeignKey("condition.condition_id"),
        comment="The condition that the patient has a record of",
        primary_key=True,
        index=True,
    )
    has_condition: Mapped[bool | None] = mapped_column(
        comment="Does the patient have this condition?"
    )
    description: Mapped[CITEXT | None] = mapped_column(
        CITEXT, comment="The description of the patient's condition"
    )
    age_of_onset: Mapped[float | None] = mapped_column(
        comment="The age in years, when a patient first started experiencing "
                "this condition",
        index=True,
    )
    age_of_presentation: Mapped[float | None] = mapped_column(
        comment="The age in years, when a person first presented this condition "
                "to a healthcare professional",
        index=True,
    )
    onset_symptoms: Mapped[str | None] = mapped_column(
        comment="The symptoms that the patient experienced when they first "
                "started experiencing this condition"
    )

    # -- Relationships
    # Associations to the individual and condition
    individual: Mapped["Individual"] = relationship(
        "Individual",
        back_populates="conditions",
    )
    condition: Mapped["Condition"] = relationship(
        "Condition",
        back_populates="individuals",
    )

    # Links to mutations
    individual_variant_condition_links: Mapped[
        Optional[list["IndividualVariantConditionLink"]]
    ] = relationship(
        "IndividualVariantConditionLink",
        back_populates="individual_condition",
        overlaps="individual_condition,individual_variant_condition_links,individual_variant",
        # noqa: E501
    )

    __table_args__ = (
        CheckConstraint("age_of_onset >= 0", name="age_of_onset_not_negative"),
        CheckConstraint(
            "age_of_presentation >= 0", name="age_of_presentation_not_negative"
        ),
        {
            "comment": "An association table between individuals and conditions that represents"
                       "a record that an individual has reported having this condition or not",
        },
    )


__all__ = [
    "IndividualCondition",
]
