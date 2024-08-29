from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_database_models.database.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .individuals import IndividualToPublication
    from .variants import PublicationVariant


class Publication(Base):
    __tablename__ = "publication"

    publication_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[CITEXT | None] = mapped_column(CITEXT)
    first_author: Mapped[CITEXT | None] = mapped_column(CITEXT)
    reference: Mapped[str | None] = mapped_column(unique=True)
    doi: Mapped[str | None] = mapped_column(unique=True)
    year: Mapped[int | None]

    individuals: Mapped[list["IndividualToPublication"]] = relationship(
        "IndividualToPublication",
        back_populates="publication",
    )
    variants: Mapped[list["PublicationVariant"]] = relationship(
        "PublicationVariant",
        back_populates="publication",
    )
    databases: Mapped[list["PublicationToDatabase"]] = relationship(
        "PublicationToDatabase",
        back_populates="publication",
    )

    __table_args__ = (
        CheckConstraint(
            # at least one of the following must be not null
            "NOT ("
            "title IS NULL AND "
            "first_author IS NULL AND "
            "reference IS NULL AND "
            "year IS NULL AND "
            "doi IS NULL)",
            name="row_not_null",
        ),
        CheckConstraint(
            # doi must match the doi regex
            f"doi IS NULL OR (doi ~ '{r'^10.\d{4,9}\/[-._;()\/:\w]+$'}')",
            name="publication_doi_regex",
        ),
    )


class PublicationDatabase(Base):
    __tablename__ = "publication_database"

    database_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(CITEXT, unique=True)
    origin_url: Mapped[str] = mapped_column(CITEXT, unique=True)
    resource_uri: Mapped[str] = mapped_column(CITEXT, unique=True)

    publications: Mapped[list["PublicationToDatabase"]] = relationship(
        "PublicationToDatabase",
        back_populates="database",
    )


class PublicationToDatabase(Base):
    __tablename__ = "publication_to_database"

    publication_id: Mapped[int] = mapped_column(
        ForeignKey("publication.publication_id"), primary_key=True
    )
    database_id: Mapped[int] = mapped_column(
        ForeignKey("publication_database.database_id"),
        primary_key=True,
        index=True,
    )
    resource_id: Mapped[str] = mapped_column()

    publication: Mapped[Publication] = relationship(
        "Publication", back_populates="databases"
    )
    database: Mapped[PublicationDatabase] = relationship(
        "PublicationDatabase", back_populates="publications"
    )

    __table_args__ = (
        UniqueConstraint(
            "resource_id",
            "database_id",
            name="uq_publication_to_database_resource_id_unique_per_database",
        ),
    )


__all__ = ["Publication", "PublicationDatabase", "PublicationToDatabase"]
