import re
from typing import TYPE_CHECKING, Literal, Any, Callable

from hgvs.easy import parser
from hgvs.location import (
    BaseOffsetPosition,
)
from hgvs.parser import Parser
from hgvs.sequencevariant import SequenceVariant
from parsley import _GrammarWrapper
from sqlalchemy import (
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import INT4RANGE, Range, CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cpvt_website_models.database.base import Base
from Bio.SeqUtils import seq1

if TYPE_CHECKING:  # pragma: no cover
    from cpvt_website_models.models import Variant


# use this dictionary to map the molecular consequence to the id
def edit_type_ids():
    return {
        "Identical": 1,
        "Substitution": 2,
        "Deletion-Insertion": 3,
        "Deletion": 4,
        "Insertion": 5,
        "Duplication": 6,
        "Inversion": 7,
        "Conversion": 8,
        "Copy": 9,
        "Frameshift": 10,
        "Extension": 11,
        "Special": 12,
        "Unknown": 13,
    }


_molecular_consequence_dict = edit_type_ids()
ARBITRARY_MAX_VARCHAR_LENGTH = 2048


def strip_nan(any_dict: dict, *, ignore_keys: set[str] = None):
    if ignore_keys is None:
        ignore_keys = set()

    return {k: v for k, v in any_dict.items() if v is not None or k in ignore_keys}


class EditType(Base):
    __tablename__ = "edit_type"

    edit_type_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(CITEXT, unique=True)
    description: Mapped[str | None] = mapped_column()

    __table_args__ = (
        {
            "comment": "What the mutation does at the molecular level - "
            "e.g. missense, nonsense, frameshift, etc.",
        },
    )


class SequenceVariantDb(
    Base,
):
    """
    A sequence variant parsed by the python or rust hgvs library.
    """

    __tablename__ = "sequence_variant"

    _molecular_consequence_dict = _molecular_consequence_dict

    def __init__(
        self,
        *,
        variant_g: SequenceVariant | None = None,
        variant_c: SequenceVariant | None = None,
        variant_p: SequenceVariant | None = None,
        reference_sequence_id_c: int | None = None,
        reference_sequence_id_g: int | None = None,
        reference_sequence_id_p: int | None = None,
        grammar: Callable[[Any], _GrammarWrapper] | None = None,
        **kwargs,
    ):
        """
        Arguments for:
        `coding_transcript, pos_class, start_class, end_class, edit_class`
        are required to be passed in kwargs - these are foreign keys and
        cannot be determined by the sequence variant object.
        """

        g_args = {}

        if variant_g is not None:
            g_args = strip_nan(
                {
                    "g_reference_sequence_id": reference_sequence_id_g,
                    "g_edit_type": self._determine_molecular_consequence_id(
                        grammar, str(variant_g)
                    ),
                    "g_posedit_str": str(variant_g.posedit)
                    if len(str(variant_g.posedit)) < ARBITRARY_MAX_VARCHAR_LENGTH
                    else None,
                    "g_pos_interval": Range(
                        variant_g.posedit.pos.start.base,
                        variant_g.posedit.pos.end.base,
                        bounds="[]",
                    ),
                    "g_hgvs_string": str(variant_g),
                }
            )
            self._add_edit_info(variant_g, g_args, "g")

        c_args = {}

        if variant_c is not None:
            c_args = {
                "c_reference_sequence_id": reference_sequence_id_c,
                "c_edit_type": self._determine_molecular_consequence_id(
                    grammar, str(variant_c)
                ),
                "c_posedit_str": str(variant_c.posedit),
                "c_pos_interval": Range(
                    variant_c.posedit.pos.start.base,
                    variant_c.posedit.pos.end.base,
                    bounds="[]",
                ),
                "c_hgvs_string": str(variant_c),
            }
            # add start and end offsets if they exist
            if isinstance(variant_c.posedit.pos.start, BaseOffsetPosition):
                c_args["c_start_offset"] = variant_c.posedit.pos.start.offset
            if isinstance(variant_c.posedit.pos.end, BaseOffsetPosition):
                c_args["c_end_offset"] = variant_c.posedit.pos.end.offset

            self._add_edit_info(variant_c, c_args, "c")

        p_args = {}

        if variant_p is not None:
            p_args = {
                "p_reference_sequence_id": reference_sequence_id_p,
                "p_edit_type": self._determine_molecular_consequence_id(
                    grammar, str(variant_p)
                ),
                "p_posedit_str": str(variant_p.posedit),
                "p_pos_interval": Range(
                    variant_p.posedit.pos.start.base,
                    variant_p.posedit.pos.end.base,
                    bounds="[]",
                ),
                "p_start_aa": variant_p.posedit.pos.start.aa,
                "p_end_aa": variant_p.posedit.pos.end.aa,
                "p_hgvs_string": str(variant_p),
            }
            self._add_edit_info(variant_p, p_args, "p")

        super().__init__(**{**g_args, **c_args, **p_args, **kwargs})

    @staticmethod
    def _add_edit_info(variant: SequenceVariant, all_args: dict, sv_type: str):
        # add edit information if the property exists
        if (
            hasattr(variant.posedit.edit, "ref")
            and variant.posedit.edit.ref is not None
            and len(str(variant.posedit.edit.ref)) < ARBITRARY_MAX_VARCHAR_LENGTH
        ):
            all_args[f"{sv_type}_edit_ref"] = variant.posedit.edit.ref
        if (
            hasattr(variant.posedit.edit, "alt")
            and variant.posedit.edit.alt is not None
            and len(str(variant.posedit.edit.alt)) < ARBITRARY_MAX_VARCHAR_LENGTH
        ):
            all_args[f"{sv_type}_edit_alt"] = variant.posedit.edit.alt

        if variant.type == "p":
            if (
                hasattr(variant.posedit.pos.start, "aa")
                and variant.posedit.pos.start is not None
            ):
                all_args["p_start_aa"] = variant.posedit.pos.start.aa
            if (
                hasattr(variant.posedit.pos.end, "aa")
                and variant.posedit.pos.end is not None
            ):
                all_args["p_end_aa"] = variant.posedit.pos.end.aa
            if (
                hasattr(variant.posedit.edit, "init_met")
                and variant.posedit.edit.init_met is not None
            ):
                all_args["p_edit_init_met"] = variant.posedit.edit.init_met

    def _determine_molecular_consequence_id(
        self, grammar: Callable[[Any], _GrammarWrapper] | None, hgvs_string: str
    ) -> str:
        """
        Get the molecular consequence of the sequence variant
        """
        variant_no_accn = hgvs_string.split(":", 1)[1]

        try:
            edit_type = grammar(variant_no_accn).typed_posedit()[1]
        except Exception:
            print(
                f"Error parsing molecular consequence {variant_no_accn}. Setting to 'Unknown'"
            )
            # some error occurred, set to unknown
            edit_type = "Unknown"

        return self._molecular_consequence_dict.get(edit_type, 13)

    @staticmethod
    def _remove_accn(variant):
        return variant.split(":", 1)[1]

    def sequence_variant(
        self, *, hp: Parser | None = None, sv_type: Literal["g", "c", "p"]
    ) -> SequenceVariant | None:
        """
        Convert the sequence variant in the database to a SequenceVariant object
        """
        if hp is None:
            hp = parser

        if sv_type == "g":
            str_to_parse = self.g_hgvs_string
        elif sv_type == "c":
            str_to_parse = self.c_hgvs_string
        elif sv_type == "p":
            str_to_parse = self.p_hgvs_string
        else:
            raise ValueError(f"Invalid sequence variant type: {sv_type}")

        try:
            sv = hp.parse(str_to_parse)
            return sv
        except Exception:
            return None

    sequence_variant_id: Mapped[int] = mapped_column(
        primary_key=True,
        comment="Primary key for the sequence variant",
    )

    # GENOMIC
    g_reference_sequence_id: Mapped[int | None] = mapped_column(
        ForeignKey("uta.seq_anno.seq_anno_id"),
        comment="The reference sequence from the UTA database. "
        "Foreign key to seq_anno.seq_anno_id, which contains the reference "
        "sequence names.",
        index=True,
    )
    g_edit_type: Mapped[int | None] = mapped_column(
        ForeignKey("edit_type.edit_type_id"),
        index=True,
        comment="The edit type for the sequence variant. ",
    )
    g_posedit_str: Mapped[str | None] = mapped_column(
        index=True, comment="For protein sequences. The posedit string."
    )
    g_pos_interval: Mapped[Range[int] | None] = mapped_column(
        INT4RANGE,
        comment="From an hgvs PosEdit.pos object. This is the pos.start.base "
        "and the pos.end.base values.",
    )
    g_edit_ref: Mapped[str | None] = mapped_column(
        index=True, comment="From an hgvs Edit object. The edit.ref value."
    )
    g_edit_alt: Mapped[str | None] = mapped_column(
        index=True, comment="From an hgvs Edit object. The edit.alt value."
    )
    g_hgvs_string: Mapped[str | None] = mapped_column(
        index=True,
        comment="The normalized hgvs string for the sequence variant",
    )

    # CODING
    c_reference_sequence_id: Mapped[int | None] = mapped_column(
        ForeignKey("uta.seq_anno.seq_anno_id"),
        comment="The reference sequence from the UTA database. "
        "Foreign key to seq_anno.seq_anno_id, which contains the reference "
        "sequence names.",
        index=True,
    )
    c_edit_type: Mapped[int | None] = mapped_column(
        ForeignKey("edit_type.edit_type_id"),
        index=True,
        comment="The edit type for the sequence variant. ",
    )
    c_posedit_str: Mapped[str | None] = mapped_column(
        index=True, comment="For protein sequences. The posedit string."
    )
    c_pos_interval: Mapped[Range[int] | None] = mapped_column(
        INT4RANGE,
        comment="From an hgvs PosEdit.pos object. This is the pos.start.base "
        "and the pos.end.base values.",
    )
    c_start_offset: Mapped[int | None] = mapped_column(
        comment="For cDNA sequences intronic variants. Otherwise null."
    )
    c_end_offset: Mapped[int | None] = mapped_column(
        comment="For cDNA sequences intronic variants. Otherwise null."
    )
    c_edit_ref: Mapped[str | None] = mapped_column(
        index=True, comment="From an hgvs Edit object. The edit.ref value."
    )
    c_edit_alt: Mapped[str | None] = mapped_column(
        index=True, comment="From an hgvs Edit object. The edit.alt value."
    )
    c_hgvs_string: Mapped[str | None] = mapped_column(
        index=True,
        comment="The normalized hgvs string for the sequence variant",
    )

    # PROTEIN
    p_reference_sequence_id: Mapped[int | None] = mapped_column(
        ForeignKey("uta.seq_anno.seq_anno_id"),
        comment="The reference sequence from the UTA database. "
        "Foreign key to seq_anno.seq_anno_id, which contains the reference "
        "sequence names.",
        index=True,
    )
    p_edit_type: Mapped[int | None] = mapped_column(
        ForeignKey("edit_type.edit_type_id"),
        index=True,
        comment="The edit type for the sequence variant. ",
    )
    p_posedit_str: Mapped[str | None] = mapped_column(
        index=True, comment="For protein sequences. The posedit string."
    )

    p_pos_interval: Mapped[Range[int] | None] = mapped_column(
        INT4RANGE,
        comment="From an hgvs PosEdit.pos object. This is the pos.start.base "
        "and the pos.end.base values.",
    )
    # NO INDEXES for the following columns becausew
    # protein consequences are tricky for hgvs package - just search based on
    # the posedit_string or hgvs_string
    p_start_aa: Mapped[str | None] = mapped_column(
        comment="For protein sequences. The start amino acid. "
        "Equivalent to edit.ref, for non protein sequences."
    )
    p_end_aa: Mapped[str | None] = mapped_column(
        comment="For protein sequences. The end amino acid."
        "Equivalent to edit.alt, for non protein sequences."
    )
    p_edit_ref: Mapped[str | None] = mapped_column(
        comment="From an hgvs Edit object. The edit.ref value."
    )
    p_edit_alt: Mapped[str | None] = mapped_column(
        comment="From an hgvs Edit object. The edit.alt value."
    )
    p_edit_init_met: Mapped[bool | None] = mapped_column(
        comment="From an hgvs Edit object. The edit.init_met value."
    )
    p_hgvs_string: Mapped[str | None] = mapped_column(
        index=True,
        comment="The normalized hgvs string for the sequence variant",
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------
    variant: Mapped[list["Variant"]] = relationship(
        "Variant",
        back_populates="sequence_variant",
    )
    edit_type_c: Mapped["EditType"] = relationship(
        "EditType",
        foreign_keys=[c_edit_type],
    )
    edit_type_g: Mapped["EditType"] = relationship(
        "EditType",
        foreign_keys=[g_edit_type],
    )
    edit_type_p: Mapped["EditType"] = relationship(
        "EditType",
        foreign_keys=[p_edit_type],
    )
    protein_consequence: Mapped["ProteinConsequence"] = relationship(
        "ProteinConsequence",
    )

    __table_args__ = (
        # gist index for range type
        Index(
            "idx_sequence_variant_g_pos_interval",
            g_pos_interval,
            postgresql_using="gist",
        ),
        Index(
            "idx_sequence_variant_c_pos_interval",
            c_pos_interval,
            postgresql_using="gist",
        ),
        Index(
            "idx_sequence_variant_p_pos_interval",
            p_pos_interval,
            postgresql_using="gist",
        ),
        # Triple UNIEQUE constraint on all 3 hgvs strings
        UniqueConstraint(
            "g_hgvs_string",
            "c_hgvs_string",
            "p_hgvs_string",
            name="uq_sequence_variant_hgvs_strings",
        ),
        # can't have all 3 be null
        CheckConstraint(
            "g_hgvs_string IS NOT NULL OR c_hgvs_string IS NOT NULL OR p_hgvs_string IS NOT NULL",
            name="ck_sequence_variant_hgvs_strings",
        ),
        {
            "comment": "A sequence variant parsed and validated by the python "
            "or rust hgvs library.",
        },
    )


hgvs_aa3 = set(
    "Ala Cys Asp Glu Phe Gly His Ile Lys Leu Met Asn Pro Gln Arg Ser Thr Val Trp Tyr Asx Glx Xaa Sec".split()
) | {"Ter"}


class ProteinConsequence(Base):
    """
    A sequence variant parsed by the python or rust hgvs library.
    """

    __tablename__ = "protein_consequence"

    def __init__(
        self,
        *,
        sequence_variant: SequenceVariantDb | SequenceVariant = None,
        **kwargs,
    ):
        if sequence_variant is None:
            super().__init__(**kwargs)
            return

        if isinstance(sequence_variant, SequenceVariant):
            self._create_from_sequence_variant(sequence_variant)
        elif isinstance(sequence_variant, SequenceVariantDb):
            self._create_from_sequence_variant_db(sequence_variant)
        else:
            raise ValueError(
                "sequence_variant must be a SequenceVariant or "
                "SequenceVariantDb object"
            )

        super().__init__(**kwargs)

    def _create_from_sequence_variant(self, sequence_variant: SequenceVariant):
        if sequence_variant.type != "p":
            raise ValueError("Sequence variant must be a protein sequence variant")

        # hgvs python package gives the AA3 code by default in the
        # str(variant.posedit) - use regex and convert all to 1 letter code
        posedit_str = str(sequence_variant.posedit)

        # strip out any parentheses
        posedit_str = posedit_str.replace("(", "").replace(")", "")

        self.posedit_aa3 = posedit_str

        # remove all non A-Za-z characters with regex
        aa3_codes = re.findall("[A-Z][a-z]{2}", posedit_str)

        # Convert each 3-letter code to a 1-letter code and replace it in the string
        for aa3 in aa3_codes:
            if aa3 not in hgvs_aa3:
                raise ValueError(f"Invalid AA3 code: {aa3}")
            aa1 = seq1(aa3)
            posedit_str = posedit_str.replace(aa3, aa1)

        self.posedit_aa1 = posedit_str

    def _create_from_sequence_variant_db(self, sequence_variant: SequenceVariantDb):
        if sequence_variant.p_hgvs_string is None:
            raise ValueError("Sequence variant must be a protein sequence variant")

        sv = sequence_variant.sequence_variant(sv_type="p")

        if sv is None:
            raise ValueError("Could not parse sequence variant")

        if sequence_variant.sequence_variant_id is not None:
            self.protein_consequence_id = sequence_variant.sequence_variant_id

        self._create_from_sequence_variant(sv)

    protein_consequence_id: Mapped[int] = mapped_column(
        ForeignKey("sequence_variant.sequence_variant_id"),
        primary_key=True,
    )
    posedit_aa1: Mapped[str] = mapped_column(
        comment="The Posedit string using the 1 letter amino acid code."
    )
    posedit_aa3: Mapped[str] = mapped_column(
        comment="The Posedit string using the 3 letter amino acid code."
    )

    __table_args__ = (
        {
            "comment": "For search purposes, store the protein consequence in "
            "both 1 letter and 3 letter amino acid codes. Not normalized. "
            "Use this in Algolia or other search engines in addition to the "
            "normalized hgvs string.",
        },
    )


__all__ = ["SequenceVariantDb", "EditType", "edit_type_ids", "ProteinConsequence"]
