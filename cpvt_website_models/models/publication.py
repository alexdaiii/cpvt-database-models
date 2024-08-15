from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base

if TYPE_CHECKING:
    from .individuals import IndividualToPublication
    from .variants import PublicationVariant


class Publication(Base):
    __tablename__ = "publication"

    publication_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[CITEXT | None] = mapped_column(CITEXT)
    first_author: Mapped[CITEXT | None] = mapped_column(CITEXT)
    pmid: Mapped[int | None] = mapped_column(unique=True)
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

    __table_args__ = (
        CheckConstraint(
            # at least one of the following must be not null
            "NOT ("
            "title IS NULL AND "
            "first_author IS NULL AND "
            "pmid IS NULL AND "
            "reference IS NULL AND "
            "year IS NULL AND "
            "doi IS NULL)",
            name="row_not_null",
        ),
        CheckConstraint(
            # pmid must be a positive integer
            "pmid IS NULL OR (pmid > 0)",
            name="publication_pmid_positive",
        ),
        CheckConstraint(
            # doi must match the doi regex
            "doi IS NULL OR (" "doi ~ '^10.\\d{4,9}/[-._;()/:\\w]+$')",
            name="publication_doi_regex",
        ),
    )


__all__ = ["Publication"]
