"""Table management routes."""

import uuid
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from ..models import SchemaUpdate, TableCreate
from ..services.table_service import (
    SchemaValidationError,
    TableExistsError,
    TableNotFoundError,
    TableService,
)

tables_bp = Blueprint("tables", __name__, url_prefix="/tables")


def validate_uuid(*param_names: str) -> Callable:
    """Decorator to validate UUID format for path parameters.

    Args:
        *param_names: Names of path parameters to validate as UUIDs.

    Returns:
        Decorator function that validates the specified parameters.
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for param_name in param_names:
                if param_name in kwargs:
                    try:
                        uuid.UUID(kwargs[param_name])
                    except ValueError:
                        return jsonify({"error": f"Invalid UUID format for {param_name}"}), 400
            return f(*args, **kwargs)

        return wrapper

    return decorator


@tables_bp.route("", methods=["POST"])
def create_table() -> tuple[Response, int]:
    """Create a new table with custom schema.

    Request body:
        {"name": "customers", "columns": [{"name": "email", "type": "string"}, ...]}

    Returns:
        201: {"id": "<table_id>"}
        400: Validation error
        409: Table already exists
    """
    try:
        data = TableCreate.model_validate(request.get_json())
    except ValidationError as e:
        # Convert Pydantic errors to JSON-serializable format (exclude ctx which may contain exceptions)
        errors = [{"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")} for err in e.errors()]
        return jsonify({"error": "Validation error", "details": errors}), 400

    try:
        table_id = TableService.create_table(data)
    except TableExistsError as e:
        return jsonify({"error": str(e)}), 409
    except SchemaValidationError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"id": table_id}), 201


@tables_bp.route("", methods=["GET"])
def list_tables() -> tuple[Response, int]:
    """List all tables.

    Returns:
        200: Array of table summaries
    """
    tables = TableService.list_tables()
    return jsonify([t.model_dump() for t in tables]), 200


@tables_bp.route("/<table_id>", methods=["GET"])
@validate_uuid("table_id")
def get_table(table_id: str) -> tuple[Response, int]:
    """Get table details including schema.

    Args:
        table_id: UUID of the table.

    Returns:
        200: Table details with columns
        400: Invalid UUID format
        404: Table not found
    """
    try:
        table = TableService.get_table(table_id)
    except TableNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(table.model_dump()), 200


@tables_bp.route("/<table_id>", methods=["DELETE"])
@validate_uuid("table_id")
def delete_table(table_id: str) -> tuple[Response, int]:
    """Delete a table and all its data.

    Args:
        table_id: UUID of the table.

    Returns:
        204: Successfully deleted
        400: Invalid UUID format
        404: Table not found
    """
    try:
        TableService.delete_table(table_id)
    except TableNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    return Response(status=204)


@tables_bp.route("/<table_id>/schema", methods=["PATCH"])
@validate_uuid("table_id")
def update_schema(table_id: str) -> tuple[Response, int]:
    """Update table schema by adding/removing columns.

    Request body:
        {"add_columns": [...], "remove_columns": ["column_name"]}

    Args:
        table_id: UUID of the table.

    Returns:
        200: Updated table details
        400: Validation error
        404: Table not found
    """
    try:
        data = SchemaUpdate.model_validate(request.get_json())
    except ValidationError as e:
        # Convert Pydantic errors to JSON-serializable format (exclude ctx which may contain exceptions)
        errors = [{"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")} for err in e.errors()]
        return jsonify({"error": "Validation error", "details": errors}), 400

    try:
        table = TableService.update_schema(table_id, data)
    except TableNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except SchemaValidationError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(table.model_dump()), 200
