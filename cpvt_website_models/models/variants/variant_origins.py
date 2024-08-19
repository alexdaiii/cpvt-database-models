"""
Publication(s) or dataset(s) that a variant is found in
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from cpvt_website_models.models.publication import Publication
    from .variant import Variant


class VariantsDataset(Base):
    __tablename__ = "variants_dataset"

    dataset_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(CITEXT, unique=True)
    description: Mapped[str | None] = mapped_column(CITEXT)
    url: Mapped[str | None] = mapped_column()

    variants: Mapped[list["DatasetVariant"]] = relationship(
        "DatasetVariant",
        back_populates="dataset",
    )

    __table_args__ = (
        {
            "comment": "Information about a dataset of variants",
        },
    )


class DatasetVariant(Base):
    __tablename__ = "variants_dataset_to_variant"

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("variants_dataset.dataset_id"),
        primary_key=True,
    )
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variant.variant_id"),
        primary_key=True,
        index=True,
    )

    dataset: Mapped[VariantsDataset] = relationship(
        "VariantsDataset",
        back_populates="variants",
    )
    variant: Mapped["Variant"] = relationship(
        "Variant",
        back_populates="datasets",
    )

    __table_args__ = (
        {
            "comment": "Link between a dataset and a variant",
        },
    )


class PublicationVariant(Base):
    __tablename__ = "publication_variant"

    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publication.publication_id"),
        primary_key=True,
    )
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variant.variant_id"),
        primary_key=True,
        index=True,
    )

    publication: Mapped["Publication"] = relationship(
        "Publication",
        back_populates="variants",
    )
    variant: Mapped["Variant"] = relationship(
        "Variant",
        back_populates="publications",
    )

    __table_args__ = (
        {
            "comment": "Link between a publication and a variant",
        },
    )


__all__ = [
    "VariantsDataset",
    "DatasetVariant",
    "PublicationVariant",
]
