"""Row models for CRUD operations."""

from typing import Any

from pydantic import BaseModel, Field


class RowCreate(BaseModel):
    """Request model for creating a new row."""

    data: dict[str, Any] = Field(..., min_length=1)

    model_config = {"extra": "forbid"}


class RowUpdate(BaseModel):
    """Request model for updating a row."""

    data: dict[str, Any] = Field(..., min_length=1)

    model_config = {"extra": "forbid"}


class RowResponse(BaseModel):
    """Response model for row data."""

    id: str
    data: dict[str, Any]
    created_at: str
    updated_at: str


class RowListResponse(BaseModel):
    """Response model for listing rows with pagination."""

    rows: list[RowResponse]
    total: int
    limit: int
    offset: int
