from typing import TypeVar, Literal

from pydantic import BaseModel, Field
from typing_extensions import Generic


class FilterHistogram(BaseModel):
    bin_: int = Field(
        alias="bin",
    )
    freq: int


C = TypeVar("C", bound=str)
T = TypeVar("T")


class FilterJSONB(BaseModel, Generic[C, T]):
    component: C
    values: list[T] | None = None
    queryParam: str
    histogram: list[FilterHistogram] | None = None
    label: str
    """
    The fieldset legend
    """

    shortLabel: str | None = None
    """
    Shorter label for the filter
    """

    description: str | None = None
    """
    Any additional description for the user inside a p tag
    """

    ordinal: int
    hidden: bool
    """
    Is this filter hidden by default?
    """


class FilterByIdValue(BaseModel):
    label: str
    value: int
    """
    The ID of the filter
    """
    alt_labels: list[str | None] | None = None


FilterByIdComponents = Literal["checkboxes", "combobox"]


class FilterById(FilterJSONB[FilterByIdComponents, FilterByIdValue]):
    pass


class FilterByRangeValue(BaseModel):
    min: float | None
    max: float | None


FilterByRangeComponents = Literal["range"]


class FilterByRange(FilterJSONB[FilterByRangeComponents, FilterByRangeValue]):
    pass
