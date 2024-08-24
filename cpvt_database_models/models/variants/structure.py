from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import INT4MULTIRANGE, Range
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_database_models.database.base import Base


class StructureRoot(Base):
    __tablename__ = "structure_root"

    structure_root_id: Mapped[int] = mapped_column(primary_key=True)

    structures: Mapped[list["Structure"]] = relationship(
        "Structure",
        back_populates="root",
    )


class StructureRootToProtein(Base):
    __tablename__ = "structure_root_to_protein"

    structure_root_id: Mapped[int] = mapped_column(
        ForeignKey("structure_root.structure_root_id"),
        primary_key=True,
    )
    protein_id: Mapped[int] = mapped_column(
        ForeignKey("uta.seq_anno.seq_anno_id"),
        index=True,
    )

    __table_args__ = (
        {
            "comment": "Which proteins are associated with which structure roots.",
        },
    )


class Structure(Base):
    __tablename__ = "structure"

    structure_id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(unique=True)
    symbol: Mapped[str | None] = mapped_column(unique=True)

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("structure.structure_id"),
        comment="The parent structure for this structure.",
        index=True,
    )
    root_id: Mapped[int] = mapped_column(
        ForeignKey("structure_root.structure_root_id"),
        index=True,
        comment="The root structure for this structure. WARNING: There is no "
        "check that this root is actually a root of the tree.",
    )
    residue_span: Mapped[list[Range[int]]] = mapped_column(INT4MULTIRANGE)

    root: Mapped[StructureRoot] = relationship(
        "StructureRoot",
        back_populates="structures",
    )

    __table_args__ = (
        CheckConstraint(
            "parent_id != structure_id",
            name="structure_parent_id_ne_structure_id",
        ),
        Index(
            "ix_structure_residue_span",
            residue_span,
            postgresql_using="gist",
        ),
    )


__all__ = [
    "Structure",
    "StructureRoot",
    "StructureRootToProtein",
]
