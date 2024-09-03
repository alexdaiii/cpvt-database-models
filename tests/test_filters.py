import os
from typing import Type

import pytest
from pydantic import ValidationError, BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cpvt_database_models.filters.schema import (
    FilterById,
    FilterByRange,
    FilterJSONB,
)
from cpvt_database_models.models import KVStore
from cpvt_database_models.models.views import add_views_pg

data_valid_filter: dict[str, tuple[Type[FilterJSONB], dict]] = {
    "checkboxes": (
        FilterById,
        {
            "label": "Data",
            "hidden": False,
            "values": [
                {"label": "Label", "value": 1},
                {"label": "Label2", "value": 2, "alt_labels": ["AltLabel2"]},
                {"label": "Label3", "value": 3, "alt_labels": [None]},
            ],
            "ordinal": 1,
            "component": "checkboxes",
            "queryParam": "query_param",
        },
    ),
    "combobox": (
        FilterById,
        {
            "label": "Data",
            "hidden": False,
            "values": [
                {"label": "Label", "value": 1},
                {"label": "Label2", "value": 2, "alt_labels": ["AltLabel2"]},
                {"label": "Label3", "value": 3, "alt_labels": [None]},
            ],
            "ordinal": 1,
            "component": "combobox",
            "queryParam": "query_param",
            "histogram": None,
            "shortLabel": None,
            "description": None,
        },
    ),
    "filterById, non null labels": (
        FilterById,
        {
            "label": "Data",
            "hidden": False,
            "values": [],
            "ordinal": 1,
            "component": "combobox",
            "queryParam": "query_param",
            "shortLabel": "Short Label",
            "description": "Description",
        },
    ),
    "filterByRange": (
        FilterByRange,
        {
            "label": "Data",
            "hidden": False,
            "values": [{"min": 1, "max": 2}],
            "ordinal": 1,
            "component": "range",
            "queryParam": "query_param",
            "histogram": [
                {
                    "bin": 1,
                    "freq": 100,
                },
                {
                    "bin": 2,
                    "freq": 200,
                },
            ],
            "shortLabel": None,
            "description": None,
        },
    ),
}


@pytest.mark.parametrize(
    ["filter_class", "filter_data"],
    data_valid_filter.values(),
    ids=data_valid_filter.keys(),
)
def test_valid_filter(filter_class: Type[FilterJSONB], filter_data: dict):
    # should be able to create a filter object
    filter_class(**filter_data)


invalid_data = {
    "range_for_checkbox": (
        FilterById,
        {
            "label": "Data",
            "hidden": False,
            "values": [{"label": "Label", "value": 1}],
            "ordinal": 1,
            "component": "range",
            "queryParam": "query_param",
        },
    ),
    "range_value_in_checkbox": (
        FilterById,
        {
            "label": "Data",
            "hidden": False,
            "values": [{"min": 1, "max": 2}],
            "ordinal": 1,
            "component": "checkboxes",
            "queryParam": "query_param",
        },
    ),
}


@pytest.mark.parametrize(
    ["filter_class", "filter_data"], invalid_data.values(), ids=invalid_data.keys()
)
def test_invalid_filter(filter_class: Type[FilterJSONB], filter_data: dict):
    with pytest.raises(ValidationError):
        filter_class(**filter_data)


async def test_add_filters(view_session: AsyncSession):
    import cpvt_database_models

    await add_views_pg(
        view_session,
        os.path.join(
            os.path.dirname(os.path.abspath(cpvt_database_models.__file__)),
            "filters/sql",
        ),
    )

    # the kv table should have NUM_FILTERS rows
    result = (await view_session.execute(select(KVStore))).scalars().all()

    num_filters = 3

    assert len(result) == num_filters

    class KVStoreRead(BaseModel):
        key: str
        value: list[FilterById | FilterByRange]

        model_config = ConfigDict(extra="ignore", from_attributes=True)

    # all filters values should be either a FilterById or FilterByRange in a list
    for kv in result:
        print(kv.value)

        KVStoreRead.model_validate(kv)
