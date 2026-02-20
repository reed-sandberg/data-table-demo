"""Pytest fixtures for Data Tables API tests."""

import os
import tempfile
from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from data_tables.app import create_app
from data_tables.config import config


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    """Create application for testing with temporary database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    # Override config to use temp database
    original_db_path = config.database_path
    config.database_path = db_path

    app = create_app({"TESTING": True, "DATABASE_PATH": db_path})

    yield app

    # Cleanup
    config.database_path = original_db_path
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_table_data() -> dict:
    """Sample table creation data."""
    return {
        "name": "customers",
        "columns": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "number"},
            {"name": "active", "type": "boolean"},
        ],
    }


@pytest.fixture
def created_table(client: FlaskClient, sample_table_data: dict) -> str:
    """Create a table and return its ID."""
    response = client.post("/tables", json=sample_table_data)
    assert response.status_code == 201
    return response.get_json()["id"]


@pytest.fixture
def sample_row_data() -> dict:
    """Sample row creation data."""
    return {"data": {"name": "Alice", "age": 30, "active": True}}


@pytest.fixture
def created_row(client: FlaskClient, created_table: str, sample_row_data: dict) -> tuple[str, str]:
    """Create a row and return (table_id, row_id)."""
    response = client.post(f"/tables/{created_table}/rows", json=sample_row_data)
    assert response.status_code == 201
    return created_table, response.get_json()["id"]
