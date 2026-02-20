"""Column definition models."""

from enum import Enum

from pydantic import BaseModel, Field


class ColumnType(str, Enum):
    """Supported column data types."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


class ColumnDefinition(BaseModel):
    """Definition for a table column."""

    name: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    type: ColumnType

    model_config = {"extra": "forbid"}


class ColumnResponse(BaseModel):
    """Column information in API responses."""

    id: str
    name: str
    type: ColumnType
    position: int
