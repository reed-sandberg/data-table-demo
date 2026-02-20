"""Validation service for type checking row data against column schemas."""

from __future__ import annotations

from typing import Any

from ..models.column import ColumnType


class ValidationError(Exception):
    """Raised when data validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


class ValidationService:
    """Service for validating row data against table schema."""

    @staticmethod
    def validate_value(value: Any, column_type: ColumnType, column_name: str) -> Any:
        """Validate and coerce a single value against its expected type.

        Args:
            value: The value to validate.
            column_type: Expected type from column definition.
            column_name: Name of the column (for error messages).

        Returns:
            The validated (and possibly coerced) value.

        Raises:
            ValidationError: If value cannot be validated as the expected type.
        """
        if value is None:
            return None  # Allow null values for all types

        if column_type == ColumnType.STRING:
            if not isinstance(value, str):
                actual_type = type(value).__name__
                raise ValidationError(f"Expected string for column '{column_name}', got {actual_type}", column_name)
            return value

        if column_type == ColumnType.NUMBER:
            if isinstance(value, bool):  # bool is subclass of int in Python
                raise ValidationError(f"Expected number for column '{column_name}', got boolean", column_name)
            if not isinstance(value, (int, float)):
                actual_type = type(value).__name__
                raise ValidationError(f"Expected number for column '{column_name}', got {actual_type}", column_name)
            return value

        if column_type == ColumnType.BOOLEAN:
            if not isinstance(value, bool):
                actual_type = type(value).__name__
                raise ValidationError(f"Expected boolean for column '{column_name}', got {actual_type}", column_name)
            return value

        raise ValidationError(f"Unknown column type: {column_type}", column_name)

    @staticmethod
    def validate_row_data(data: dict[str, Any], columns: dict[str, ColumnType]) -> dict[str, Any]:
        """Validate row data against table schema.

        Args:
            data: Row data to validate.
            columns: Dict mapping column names to their types.

        Returns:
            Validated data dict.

        Raises:
            ValidationError: If any field fails validation.
        """
        validated = {}

        # Check for unknown columns
        unknown_cols = set(data.keys()) - set(columns.keys())
        if unknown_cols:
            raise ValidationError(f"Unknown columns: {', '.join(sorted(unknown_cols))}")

        # Validate each provided field
        for col_name, value in data.items():
            col_type = columns[col_name]
            validated[col_name] = ValidationService.validate_value(value, col_type, col_name)

        return validated
