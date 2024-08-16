"""
This module contains the classes for variants.
"""
from .hgvs_variant import (
    SequenceVariantDb,
    EditType,
    ProteinConsequence,
    edit_type_ids
)
from .structure import (
    Structure,
    StructureRoot,
    StructureRootToProtein,
)
from .variant import (
    Variant
)
from .variant_links import (
    ClinVarVariantLinkedCondition
)
from .variant_origins import (
    VariantsDataset,
    DatasetVariant,
    PublicationVariant,
)

__all__ = [
    "SequenceVariantDb",
    "EditType",
    "ProteinConsequence",
    "edit_type_ids",
    "Structure",
    "StructureRoot",
    "StructureRootToProtein",
    "Variant",
    "ClinVarVariantLinkedCondition",
    "VariantsDataset",
    "DatasetVariant",
    "PublicationVariant",
]
