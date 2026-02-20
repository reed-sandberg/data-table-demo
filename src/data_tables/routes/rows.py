"""Row management routes."""

from typing import Any

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from ..models import RowCreate, RowUpdate
from ..services.row_service import CorruptedDataError, InvalidFilterError, RowNotFoundError, RowService
from ..services.table_service import TableNotFoundError
from ..services.validation import DataValidationError
from .tables import validate_uuid

rows_bp = Blueprint("rows", __name__, url_prefix="/tables/<table_id>/rows")


def _parse_filters() -> dict[str, Any]:
    """Parse filter parameters from query string.

    Supports format: ?filter[name]=Alice&filter[age]=30

    Returns:
        Dict mapping field names to filter values.
    """
    filters = {}
    for key, value in request.args.items():
        if key.startswith("filter[") and key.endswith("]"):
            field_name = key[7:-1]  # Extract "name" from "filter[name]"
            filters[field_name] = value
    return filters


@rows_bp.route("", methods=["GET"])
@validate_uuid("table_id")
def list_rows(table_id: str) -> tuple[Response, int]:
    """Get all rows from a table with optional filtering.

    Query params:
        - filter[column_name]=value: Filter by column value
        - limit: Max rows to return (default: 100)
        - offset: Rows to skip (default: 0)

    Args:
        table_id: UUID of the table.

    Returns:
        200: {"rows": [...], "total": N, "limit": N, "offset": N}
        400: Invalid UUID format or unknown filter column
        404: Table not found
    """
    filters = _parse_filters()
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    # Clamp limit to reasonable bounds
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)

    try:
        result = RowService.list_rows(table_id, filters=filters, limit=limit, offset=offset)
    except TableNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except InvalidFilterError as e:
        return jsonify({"error": str(e)}), 400
    except CorruptedDataError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result.model_dump()), 200


@rows_bp.route("", methods=["POST"])
@validate_uuid("table_id")
def create_row(table_id: str) -> tuple[Response, int]:
    """Insert a new row into the table.

    Request body:
        {"data": {"column_name": value, ...}}

    Args:
        table_id: UUID of the table.

    Returns:
        201: {"id": "<row_id>"}
        400: Invalid UUID format or validation error
        404: Table not found
    """
    try:
        data = RowCreate.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    try:
        row_id = RowService.create_row(table_id, data)
    except TableNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except DataValidationError as e:
        return jsonify({"error": str(e), "field": e.field}), 400

    return jsonify({"id": row_id}), 201


@rows_bp.route("/<row_id>", methods=["GET"])
@validate_uuid("table_id", "row_id")
def get_row(table_id: str, row_id: str) -> tuple[Response, int]:
    """Get a single row by ID.

    Args:
        table_id: UUID of the table.
        row_id: UUID of the row.

    Returns:
        200: Row data
        400: Invalid UUID format
        404: Table or row not found
    """
    try:
        row = RowService.get_row(table_id, row_id)
    except (TableNotFoundError, RowNotFoundError) as e:
        return jsonify({"error": str(e)}), 404
    except CorruptedDataError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(row.model_dump()), 200


@rows_bp.route("/<row_id>", methods=["PUT"])
@validate_uuid("table_id", "row_id")
def update_row(table_id: str, row_id: str) -> tuple[Response, int]:
    """Update an existing row.

    Request body:
        {"data": {"column_name": new_value, ...}}

    Args:
        table_id: UUID of the table.
        row_id: UUID of the row.

    Returns:
        200: Updated row data
        400: Invalid UUID format or validation error
        404: Table or row not found
        500: Corrupted data in database
    """
    try:
        data = RowUpdate.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    try:
        row = RowService.update_row(table_id, row_id, data)
    except (TableNotFoundError, RowNotFoundError) as e:
        return jsonify({"error": str(e)}), 404
    except DataValidationError as e:
        return jsonify({"error": str(e), "field": e.field}), 400
    except CorruptedDataError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(row.model_dump()), 200


@rows_bp.route("/<row_id>", methods=["DELETE"])
@validate_uuid("table_id", "row_id")
def delete_row(table_id: str, row_id: str) -> tuple[Response, int]:
    """Delete a row.

    Args:
        table_id: UUID of the table.
        row_id: UUID of the row.

    Returns:
        204: Successfully deleted
        400: Invalid UUID format
        404: Table or row not found
    """
    try:
        RowService.delete_row(table_id, row_id)
    except (TableNotFoundError, RowNotFoundError) as e:
        return jsonify({"error": str(e)}), 404

    return Response(status=204)
