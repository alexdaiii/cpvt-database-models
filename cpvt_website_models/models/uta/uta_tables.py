from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from cpvt_website_models.database.base import BaseBase


class TranscriptUta(BaseBase):
    __tablename__ = "transcript"

    ac: Mapped[str] = mapped_column(primary_key=True)
    origin_id: Mapped[int] = mapped_column()
    hgnc: Mapped[str] = mapped_column()
    cds_start_i: Mapped[int | None] = mapped_column()
    cds_end_i: Mapped[int | None] = mapped_column()
    cds_md5: Mapped[str | None] = mapped_column()
    added: Mapped[datetime | None] = mapped_column()

    # its on the uta schema
    __table_args__ = ({"schema": "uta"},)


class SeqAnnoUta(BaseBase):
    __tablename__ = "seq_anno"

    seq_anno_id: Mapped[int] = mapped_column(primary_key=True)
    seq_id: Mapped[int] = mapped_column()
    origin_id: Mapped[int] = mapped_column()
    ac: Mapped[str] = mapped_column()
    descr: Mapped[str] = mapped_column()

    __table_args__ = ({"schema": "uta"},)


class GeneUta(BaseBase):
    __tablename__ = "gene"

    hgnc: Mapped[str] = mapped_column(primary_key=True)
    maploc: Mapped[str | None] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    summary: Mapped[str | None] = mapped_column()
    aliases: Mapped[str | None] = mapped_column()
    added: Mapped[datetime | None] = mapped_column()

    __table_args__ = ({"schema": "uta"},)


class ExonSetUta(BaseBase):
    __tablename__ = "exon_set"

    exon_set_id: Mapped[int] = mapped_column(primary_key=True)
    tx_ac: Mapped[str] = mapped_column()
    alt_ac: Mapped[str] = mapped_column()
    alt_strand: Mapped[int] = mapped_column()
    alt_aln_method: Mapped[str] = mapped_column()
    added: Mapped[datetime | None] = mapped_column()

    __table_args__ = ({"schema": "uta"},)


class Exon(BaseBase):
    __tablename__ = "exon"

    exon_id: Mapped[int] = mapped_column(primary_key=True)
    exon_set_id: Mapped[int] = mapped_column()
    start_i: Mapped[int] = mapped_column()
    end_i: Mapped[int] = mapped_column()
    ord: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column()

    __table_args__ = ({"schema": "uta"},)


__all__ = ["TranscriptUta", "SeqAnnoUta", "GeneUta"]
