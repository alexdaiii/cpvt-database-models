"""
This module contains the classes for HGVS package parsed variants.
"""
from .sequence_variant import (SequenceVariantDb,
                               EditType,
                               ProteinConsequence,
                               edit_type_ids)

__all__ = [
    'SequenceVariantDb',
    'EditType',
    'ProteinConsequence',
    'edit_type_ids'
]
