"""Table models for create, update, and response."""

from pydantic import BaseModel, Field, field_validator

from .column import ColumnDefinition, ColumnResponse


class TableCreate(BaseModel):
    """Request model for creating a new table."""

    name: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    columns: list[ColumnDefinition] = Field(..., min_length=1, max_length=500)

    model_config = {"extra": "forbid"}

    @field_validator("columns")
    @classmethod
    def validate_unique_column_names(cls, columns: list[ColumnDefinition]) -> list[ColumnDefinition]:
        """Ensure all column names are unique within the table."""
        names = [col.name for col in columns]
        if len(names) != len(set(names)):
            raise ValueError("Column names must be unique within a table")
        return columns


class TableResponse(BaseModel):
    """Response model for table information."""

    id: str
    name: str
    columns: list[ColumnResponse]
    created_at: str
    updated_at: str


class TableListResponse(BaseModel):
    """Response model for listing tables."""

    id: str
    name: str
    column_count: int
    created_at: str


class SchemaUpdate(BaseModel):
    """Request model for updating table schema."""

    add_columns: list[ColumnDefinition] = Field(default_factory=list, max_length=500)
    remove_columns: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @field_validator("add_columns")
    @classmethod
    def validate_unique_new_columns(cls, columns: list[ColumnDefinition]) -> list[ColumnDefinition]:
        """Ensure new column names are unique among themselves."""
        names = [col.name for col in columns]
        if len(names) != len(set(names)):
            raise ValueError("New column names must be unique")
        return columns

    @field_validator("remove_columns")
    @classmethod
    def validate_remove_columns(cls, columns: list[str]) -> list[str]:
        """Ensure column names to remove are unique."""
        if len(columns) != len(set(columns)):
            raise ValueError("Duplicate column names in remove_columns")
        return columns

