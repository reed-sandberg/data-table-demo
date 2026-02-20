"""Row service for CRUD operations on table rows."""

from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from ..database import get_db, transaction
from ..models.column import ColumnType
from ..models.row import RowCreate, RowListResponse, RowResponse, RowUpdate
from .table_service import TableNotFoundError, TableService
from .validation import ValidationService


class RowNotFoundError(Exception):
    """Raised when a row is not found."""

    pass


class RowService:
    """Service for row CRUD operations."""

    @staticmethod
    def _verify_table_exists(table_id: str) -> None:
        """Verify that a table exists."""
        conn = get_db()
        row = conn.execute("SELECT id FROM tables WHERE id = ?", (table_id,)).fetchone()
        if not row:
            raise TableNotFoundError(f"Table '{table_id}' not found")

    @staticmethod
    def _get_column_types(table_id: str) -> dict[str, ColumnType]:
        """Get column types for validation."""
        type_map = TableService.get_column_types(table_id)
        return {name: ColumnType(t) for name, t in type_map.items()}

    @staticmethod
    def create_row(table_id: str, request: RowCreate) -> str:
        """Create a new row in the table.

        Args:
            table_id: The table's UUID.
            request: RowCreate with data dict.

        Returns:
            The ID of the created row.

        Raises:
            TableNotFoundError: If table doesn't exist.
            ValidationError: If data fails type validation.
        """
        RowService._verify_table_exists(table_id)

        # Validate data against schema
        column_types = RowService._get_column_types(table_id)
        validated_data = ValidationService.validate_row_data(request.data, column_types)

        row_id = str(uuid.uuid4())
        conn = get_db()

        with transaction(conn):
            conn.execute(
                "INSERT INTO rows (id, table_id, data) VALUES (?, ?, jsonb(?))",
                (row_id, table_id, json.dumps(validated_data)),
            )

        return row_id

    @staticmethod
    def get_row(table_id: str, row_id: str) -> RowResponse:
        """Get a single row by ID.

        Args:
            table_id: The table's UUID.
            row_id: The row's UUID.

        Returns:
            RowResponse with row data.

        Raises:
            TableNotFoundError: If table doesn't exist.
            RowNotFoundError: If row doesn't exist.
        """
        RowService._verify_table_exists(table_id)
        conn = get_db()

        row = conn.execute(
            "SELECT id, json(data) as data, created_at, updated_at FROM rows WHERE id = ? AND table_id = ?",
            (row_id, table_id),
        ).fetchone()

        if not row:
            raise RowNotFoundError(f"Row '{row_id}' not found in table '{table_id}'")

        return RowResponse(
            id=row["id"],
            data=json.loads(row["data"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def update_row(table_id: str, row_id: str, request: RowUpdate) -> RowResponse:
        """Update an existing row.

        Args:
            table_id: The table's UUID.
            row_id: The row's UUID.
            request: RowUpdate with new data.

        Returns:
            Updated RowResponse.

        Raises:
            TableNotFoundError: If table doesn't exist.
            RowNotFoundError: If row doesn't exist.
            ValidationError: If data fails type validation.
        """
        RowService._verify_table_exists(table_id)

        # Validate data against schema
        column_types = RowService._get_column_types(table_id)
        validated_data = ValidationService.validate_row_data(request.data, column_types)

        conn = get_db()

        with transaction(conn):
            # Get existing row
            existing = conn.execute(
                "SELECT id, json(data) as data FROM rows WHERE id = ? AND table_id = ?",
                (row_id, table_id),
            ).fetchone()

            if not existing:
                raise RowNotFoundError(f"Row '{row_id}' not found in table '{table_id}'")

            # Merge existing data with updates
            current_data = json.loads(existing["data"])
            current_data.update(validated_data)

            conn.execute(
                "UPDATE rows SET data = jsonb(?), updated_at = datetime('now') WHERE id = ?",
                (json.dumps(current_data), row_id),
            )

        return RowService.get_row(table_id, row_id)

    @staticmethod
    def delete_row(table_id: str, row_id: str) -> None:
        """Delete a row."""
        RowService._verify_table_exists(table_id)
        conn = get_db()

        with transaction(conn):
            result = conn.execute("DELETE FROM rows WHERE id = ? AND table_id = ?", (row_id, table_id))
            if result.rowcount == 0:
                raise RowNotFoundError(f"Row '{row_id}' not found in table '{table_id}'")

    @staticmethod
    def list_rows(
        table_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> RowListResponse:
        """List rows with optional filtering and pagination.

        Supports filtering via query params like ?filter[name]=Alice&filter[age]=30

        Args:
            table_id: The table's UUID.
            filters: Optional dict of column_name -> value to filter by.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.

        Returns:
            RowListResponse with rows and pagination info.

        Raises:
            TableNotFoundError: If table doesn't exist.
        """
        RowService._verify_table_exists(table_id)
        conn = get_db()

        # Build base query
        query = "SELECT id, json(data) as data, created_at, updated_at FROM rows WHERE table_id = ?"
        count_query = "SELECT COUNT(*) as total FROM rows WHERE table_id = ?"
        params: List[Any] = [table_id]
        count_params: List[Any] = [table_id]

        # Add filter conditions
        if filters:
            column_types = RowService._get_column_types(table_id)
            for field_name, field_value in filters.items():
                # Validate filter field exists in schema
                if field_name not in column_types:
                    continue  # Ignore unknown filter fields

                # Use json_extract for filtering
                col_type = column_types[field_name]
                query += " AND json_extract(data, ?) = ?"
                count_query += " AND json_extract(data, ?) = ?"

                json_path = f"$.{field_name}"

                # Coerce filter value to appropriate type
                coerced_value = RowService._coerce_filter_value(field_value, col_type)

                params.extend([json_path, coerced_value])
                count_params.extend([json_path, coerced_value])

        # Get total count
        total = conn.execute(count_query, count_params).fetchone()["total"]

        # Add pagination
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

        return RowListResponse(
            rows=[
                RowResponse(
                    id=r["id"],
                    data=json.loads(r["data"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def _coerce_filter_value(value: str, col_type: ColumnType) -> Any:
        """Coerce a filter string value to the appropriate type.

        Args:
            value: String value from query parameter.
            col_type: Expected column type.

        Returns:
            Coerced value for SQL comparison.
        """
        if col_type == ColumnType.BOOLEAN:
            return value.lower() in ("true", "1", "yes")
        if col_type == ColumnType.NUMBER:
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value  # Let SQL handle the mismatch
        return value  # STRING type
