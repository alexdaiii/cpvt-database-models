"""
Every model (except the uta models) should be able to be
added to the database without any errors.
"""

from typing import Callable

import pytest
from hgvs.easy import parser
from sqlalchemy import ForeignKey

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, relationship, Mapped

from cpvt_website_models.database import BaseBase
from cpvt_website_models.models import (
    Individual,
    IndividualSex,
    Publication,
    IndividualToPublication,
    Condition,
    IndividualCondition,
    FamilyHistoryRecord,
    KinshipName,
    FamilyMemberHistory,
    Treatment,
    IndividualOriginalExcelRow,
    TreatmentRecord,
    Variant,
    VariantInheritance,
    Zygosity,
    IndividualVariant,
    VariantsDataset,
    DatasetVariant,
    VariantClinVarInfo,
    ClinicalSignificance,
    ClinVarVariantLinkedCondition,
    EditType,
    SequenceVariantDb,
    edit_type_ids,
    ProteinConsequence,
)


def _protein_sequence_from_variant():
    sv = SequenceVariantDb(
        sequence_variant_id=1,
        variant_g=parser.parse("NC_000001.11:g.1234del"),
        variant_c=parser.parse("NM_001035.3(RYR2):c.14876G>A"),
        variant_p=parser.parse("NP_003997.1:p.Trp24Ter"),
    )

    return [
        *[
            EditType(edit_type_id=edit_type_id, name=edit_type)
            for edit_type, edit_type_id in edit_type_ids().items()
        ],
        sv,
        ProteinConsequence(
            sequence_variant=sv,
        ),
    ]


_models: dict[str, Callable[[], list[BaseBase]]] = {
    "individual": lambda: [
        IndividualSex(individual_sex_id=1, value="1"),
        Individual(
            individual_id=1,
            individual_sex_id=1,
        ),
        IndividualOriginalExcelRow(individual_id=1, original_row={"key": "value"}),
    ],
    "individual_and_publication": lambda: [
        Individual(
            individual_id=1,
        ),
        Publication(
            publication_id=2,
            title="title",
        ),
        IndividualToPublication(
            individual_id=1,
            publication_id=2,
        ),
    ],
    "individual_conditions": lambda: [
        Individual(
            individual_id=2,
        ),
        Condition(condition_id=1, condition="condition"),
        IndividualCondition(
            condition_id=1,
            individual_id=2,
            has_condition=True,
            age_of_onset=1.0,
        ),
    ],
    "individual_family_history": lambda: [
        Individual(
            individual_id=2,
        ),
        Condition(condition_id=1, condition="condition"),
        FamilyHistoryRecord(
            family_history_record_id=3,
            individual_id=2,
            condition_id=1,
            num_family_members=700,
        ),
        KinshipName(kinship_name_id=1, name="name"),
        FamilyMemberHistory(
            kinship_name_id=1,
            family_history_record_id=3,
            has_condition=False,
        ),
    ],
    "individual_treatments": lambda: [
        Individual(
            individual_id=2,
        ),
        Treatment(treatment_id=1, treatment_name="treatment"),
        TreatmentRecord(
            patient_id=2,
            treatment_id=1,
            effective=True,
            treatment_taken=True,
        ),
    ],
    "individual_variant": lambda: [
        Individual(
            individual_id=2,
        ),
        Variant(variant_id=1, hgvs_string="hgvs_string"),
        VariantInheritance(variant_inheritance_id=1, variant_inheritance="inheritance"),
        Zygosity(zygosity_id=1, zygosity="homozygous"),
        IndividualVariant(
            individual_id=2,
            variant_id=1,
            variant_inheritance_id=1,
            zygosity_id=1,
            extra_information={"key": "value"},
        ),
    ],
    "variant_origins": lambda: [
        Variant(variant_id=1, hgvs_string="hgvs_string"),
        VariantsDataset(dataset_id=2, name="name"),
        DatasetVariant(dataset_id=2, variant_id=1),
    ],
    "variant_properties": lambda: [
        Variant(variant_id=1, hgvs_string="hgvs_string"),
        VariantClinVarInfo(variant_id=1, variation_clinvar_id=2),
        ClinicalSignificance(
            clinical_significance_id=1,
            clinical_significance="variant of unknown significance",
        ),
    ],
    "variant_conditions": lambda: [
        Variant(variant_id=1, hgvs_string="hgvs_string"),
        Condition(condition_id=1, condition="condition"),
        ClinVarVariantLinkedCondition(variant_id=1, condition_id=1),
    ],
    "structure_variant": lambda: [
        *[
            EditType(edit_type_id=edit_type_id, name=edit_type)
            for edit_type, edit_type_id in edit_type_ids().items()
        ],
        SequenceVariantDb(
            sequence_variant_id=1,
            variant_g=parser.parse("NC_000001.11:g.1234del"),
            variant_c=parser.parse("NM_001035.3(RYR2):c.14876G>A"),
            variant_p=parser.parse("NP_003997.1:p.Trp24Ter"),
        ),
        Variant(
            variant_id=1,
            hgvs_string="hgvs_string",
            sequence_variant_id=1,
        ),
    ],
    "protein_consequence_manual": lambda: [
        *[
            EditType(edit_type_id=edit_type_id, name=edit_type)
            for edit_type, edit_type_id in edit_type_ids().items()
        ],
        SequenceVariantDb(
            sequence_variant_id=1,
            variant_g=parser.parse("NC_000001.11:g.1234del"),
            variant_c=parser.parse("NM_001035.3(RYR2):c.14876G>A"),
            variant_p=parser.parse("NP_003997.1:p.Trp24Ter"),
        ),
        # manual
        ProteinConsequence(
            protein_consequence_id=1,
            posedit_aa1="fb",
            posedit_aa3="foobar",
        ),
    ],
    "protein_consequence_from_sequence_variant_db": _protein_sequence_from_variant,
    "protein_consequence_from_hgvs_sequence": lambda: [
        *[
            EditType(edit_type_id=edit_type_id, name=edit_type)
            for edit_type, edit_type_id in edit_type_ids().items()
        ],
        SequenceVariantDb(
            sequence_variant_id=1,
            variant_g=parser.parse("NC_000001.11:g.1234del"),
            variant_c=parser.parse("NM_001035.3(RYR2):c.14876G>A"),
            variant_p=parser.parse("NP_003997.1:p.Trp24Ter"),
        ),
        ProteinConsequence(
            protein_consequence_id=1,
            sequence_variant=parser.parse("NP_003997.1:p.Trp24Ter"),
        ),
    ],
}


@pytest.mark.parametrize("models", _models.values(), ids=_models.keys())
async def test_model_creation(
    session: AsyncSession, models: Callable[[], list[BaseBase]]
):
    for model in models():
        session.add(model)
    await session.commit()


_protein_models: dict[str, Callable[[], ProteinConsequence]] = {
    "invalid_object_sequence_variant": lambda: ProteinConsequence(
        sequence_variant=object()
    ),
    "non_protein_sequence_variant": lambda: ProteinConsequence(
        sequence_variant=parser.parse("NC_000001.11:g.1234del")
    ),
    "sequence_variant_db_no_protein": lambda: ProteinConsequence(
        sequence_variant=SequenceVariantDb(
            sequence_variant_id=1,
            variant_g=parser.parse("NC_000001.11:g.1234del"),
            variant_c=parser.parse("NM_001035.3(RYR2):c.14876G>A"),
        )
    ),
}


@pytest.mark.parametrize("models", _protein_models.values(), ids=_protein_models.keys())
def test_protein_consequence_invalid(models: Callable[[], ProteinConsequence]):
    with pytest.raises(ValueError):
        models()


def test_models_base(session: AsyncSession):
    class Hero(BaseBase):
        __tablename__ = "hero"

        hero_id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()

        sidekicks: Mapped[list["Sidekick"] | None] = relationship(
            "Sidekick",
            back_populates="hero",
        )

    class Sidekick(BaseBase):
        __tablename__ = "sidekick"

        sidekick_id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()
        hero_id: Mapped[int] = mapped_column(ForeignKey("hero.hero_id"))

        hero: Mapped["Hero"] = relationship(
            "Hero",
            back_populates="sidekicks",
        )

    hero = Hero(
        hero_id=1,
        name="hero",
        sidekicks=[
            Sidekick(
                sidekick_id=1,
                name="sidekick1",
            ),
            Sidekick(
                sidekick_id=2,
                name="sidekick2",
            ),
        ],
    )

    # the hero object should give a string without any sidekicks
    assert (
        str(hero)
        == {
            "hero_id": 1,
            "name": "hero",
        }.__str__()
    )

    # test the repr method
    assert [hero].__str__() == [
        {
            "hero_id": 1,
            "name": "hero",
        }
    ].__str__()
