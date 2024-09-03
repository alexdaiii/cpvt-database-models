import sys

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.parametrize(
    "views",
    [
        "variant_num_individuals_v",
        "variant_to_exon_v",
        "p_variant_to_structure_v",
        "variant_view_mv",
        "protein_consequence_mv",
        "individuals_mv",
        "cpvt_patients_v",
    ],
)
async def test_views_created(view_session: AsyncSession, views: str):
    result = (
        (await view_session.execute(text(f"SELECT * FROM {views}"))).scalars().all()
    )

    assert result is not None


async def test_execute_file_import_error(monkeypatch, session: AsyncSession):
    from cpvt_database_models.models.views import add_views

    monkeypatch.setitem(sys.modules, "sqlparse", None)

    with pytest.raises(ImportError):
        await add_views.execute_file(session, "None.sql")
