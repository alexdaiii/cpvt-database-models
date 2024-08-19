from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .variants import Variant


class PathogenicityPredictor(Base):
    __tablename__ = "pathogenicity_predictor"

    predictor_id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(unique=True)

    predictions: Mapped[list["PathogenicityPrediction"]] = relationship(
        "PathogenicityPrediction",
        back_populates="predictor",
    )

    __table_args__ = (
        {
            "comment": "Pathogenicity predictor models",
        },
    )


class PathogenicityPrediction(Base):
    __tablename__ = "pathogenicity_prediction"

    predictor_id: Mapped[int] = mapped_column(
        ForeignKey("pathogenicity_predictor.predictor_id"), primary_key=True
    )
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variant.variant_id"), primary_key=True, index=True
    )
    prediction: Mapped[str | None] = mapped_column()
    score: Mapped[float | None] = mapped_column()

    variant: Mapped["Variant"] = relationship(
        "Variant",
        back_populates="predictions",
    )
    predictor: Mapped["PathogenicityPredictor"] = relationship(
        "PathogenicityPredictor",
        back_populates="predictions",
    )

    __table_args__ = (
        CheckConstraint(
            "prediction IS NOT NULL OR score IS NOT NULL",
            name="prediction_or_score_not_null",
        ),
        {
            "comment": "VUS predictor models",
        },
    )


__all__ = [
    "PathogenicityPredictor",
    "PathogenicityPrediction",
]
