"""Table service for CRUD operations on tables and schema management."""

import uuid
from sqlite3 import IntegrityError

from ..config import config
from ..database import get_db, transaction
from ..models import SchemaUpdate, TableCreate
from ..models.column import ColumnResponse
from ..models.table import TableListResponse, TableResponse


class TableNotFoundError(Exception):
    """Raised when a table is not found."""

    pass


class TableExistsError(Exception):
    """Raised when attempting to create a table that already exists."""

    pass


class SchemaValidationError(Exception):
    """Raised when schema update validation fails."""

    pass


class TableService:
    """Service for table CRUD operations."""

    @staticmethod
    def create_table(request: TableCreate) -> str:
        """Create a new table with the given schema.

        Args:
            request: TableCreate model with name and columns.

        Returns:
            The ID of the created table.

        Raises:
            TableExistsError: If a table with this name already exists.
            SchemaValidationError: If column count exceeds maximum.
        """
        if len(request.columns) > config.max_columns_per_table:
            raise SchemaValidationError(f"Maximum {config.max_columns_per_table} columns allowed per table")

        table_id = str(uuid.uuid4())
        conn = get_db()

        with transaction(conn):
            try:
                conn.execute(
                    "INSERT INTO tables (id, name) VALUES (?, ?)",
                    (table_id, request.name),
                )
            except IntegrityError as e:
                raise TableExistsError(f"Table '{request.name}' already exists") from e

            for position, col in enumerate(request.columns):
                col_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO columns (id, table_id, name, type, position) VALUES (?, ?, ?, ?, ?)",
                    (col_id, table_id, col.name, col.type.value, position),
                )

        return table_id

    @staticmethod
    def get_table(table_id: str) -> TableResponse:
        """Get table details by ID.

        Args:
            table_id: The table's UUID.

        Returns:
            TableResponse with table info and columns.

        Raises:
            TableNotFoundError: If table doesn't exist.
        """
        conn = get_db()

        row = conn.execute("SELECT id, name, created_at, updated_at FROM tables WHERE id = ?", (table_id,)).fetchone()

        if not row:
            raise TableNotFoundError(f"Table '{table_id}' not found")

        columns = conn.execute(
            "SELECT id, name, type, position FROM columns WHERE table_id = ? ORDER BY position",
            (table_id,),
        ).fetchall()

        return TableResponse(
            id=row["id"],
            name=row["name"],
            columns=[
                ColumnResponse(id=c["id"], name=c["name"], type=c["type"], position=c["position"]) for c in columns
            ],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def list_tables() -> list[TableListResponse]:
        """List all tables with basic info."""
        conn = get_db()

        rows = conn.execute(
            """
            SELECT t.id, t.name, t.created_at, COUNT(c.id) as column_count
            FROM tables t
            LEFT JOIN columns c ON t.id = c.table_id
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """
        ).fetchall()

        return [
            TableListResponse(id=r["id"], name=r["name"], column_count=r["column_count"], created_at=r["created_at"])
            for r in rows
        ]

    @staticmethod
    def delete_table(table_id: str) -> None:
        """Delete a table and all its data.

        Args:
            table_id: The table's UUID.

        Raises:
            TableNotFoundError: If table doesn't exist.
        """
        conn = get_db()

        with transaction(conn):
            result = conn.execute("DELETE FROM tables WHERE id = ?", (table_id,))
            if result.rowcount == 0:
                raise TableNotFoundError(f"Table '{table_id}' not found")

    @staticmethod
    def update_schema(table_id: str, request: SchemaUpdate) -> TableResponse:
        """Update table schema by adding/removing columns.

        Args:
            table_id: The table's UUID.
            request: SchemaUpdate with columns to add/remove.

        Returns:
            Updated TableResponse.

        Raises:
            TableNotFoundError: If table doesn't exist.
            SchemaValidationError: If update would violate constraints.
        """
        conn = get_db()

        # Verify table exists
        table_row = conn.execute("SELECT id, name FROM tables WHERE id = ?", (table_id,)).fetchone()
        if not table_row:
            raise TableNotFoundError(f"Table '{table_id}' not found")

        # Get existing columns
        existing_cols = conn.execute(
            "SELECT name, position FROM columns WHERE table_id = ? ORDER BY position", (table_id,)
        ).fetchall()
        existing_names = {c["name"] for c in existing_cols}
        max_position = max((c["position"] for c in existing_cols), default=-1)

        # Validate remove_columns exist
        for col_name in request.remove_columns:
            if col_name not in existing_names:
                raise SchemaValidationError(f"Column '{col_name}' does not exist")

        # Validate add_columns don't conflict
        remaining_cols = existing_names - set(request.remove_columns)
        for col in request.add_columns:
            if col.name in remaining_cols:
                raise SchemaValidationError(f"Column '{col.name}' already exists")
            remaining_cols.add(col.name)

        # Check total column count
        final_count = len(remaining_cols)
        if final_count > config.max_columns_per_table:
            raise SchemaValidationError(f"Maximum {config.max_columns_per_table} columns allowed")

        with transaction(conn):
            # Remove columns
            if request.remove_columns:
                placeholders = ",".join("?" * len(request.remove_columns))
                conn.execute(
                    f"DELETE FROM columns WHERE table_id = ? AND name IN ({placeholders})",
                    [table_id, *request.remove_columns],
                )

                # Update row data to remove these columns using json_remove()
                # This is O(N) at the database level with a single UPDATE statement
                # Build json_remove paths: json_remove(data, '$.col1', '$.col2', ...)
                json_paths = [f"$.{col_name}" for col_name in request.remove_columns]
                conn.execute(
                    f"UPDATE rows SET data = jsonb(json_remove(data, {','.join('?' * len(json_paths))})), "
                    "updated_at = datetime('now') WHERE table_id = ?",
                    [*json_paths, table_id],
                )

            # Add new columns
            for col in request.add_columns:
                max_position += 1
                col_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO columns (id, table_id, name, type, position) VALUES (?, ?, ?, ?, ?)",
                    (col_id, table_id, col.name, col.type.value, max_position),
                )

            # Update table timestamp
            conn.execute("UPDATE tables SET updated_at = datetime('now') WHERE id = ?", (table_id,))

        return TableService.get_table(table_id)

    @staticmethod
    def get_column_types(table_id: str) -> dict[str, str]:
        """Get a mapping of column names to their types for a table.

        Args:
            table_id: The table's UUID.

        Returns:
            Dict mapping column names to type strings.
        """
        conn = get_db()
        columns = conn.execute("SELECT name, type FROM columns WHERE table_id = ?", (table_id,)).fetchall()
        return {c["name"]: c["type"] for c in columns}
