"""
Contains association tables (and other tables that are related to the association
tables for Individuals) to other tables NOT in the individuals directory.
"""
from .individual_condition import (
    IndividualCondition
)
from .individual_variants import (
    VariantInheritance,
    Zygosity,
    IndividualVariant,
)
from .individual_variant_condition_link import IndividualVariantConditionLink

__all__ = [
    "IndividualCondition",
    "VariantInheritance",
    "Zygosity",
    "IndividualVariant",
    "IndividualVariantConditionLink",
]
