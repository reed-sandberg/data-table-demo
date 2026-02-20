"""Tests for row management endpoints."""

import pytest
from flask.testing import FlaskClient


class TestCreateRow:
    """Tests for POST /tables/<id>/rows."""

    def test_create_row_success(self, client: FlaskClient, created_table: str, sample_row_data: dict):
        """Successfully create a row."""
        response = client.post(f"/tables/{created_table}/rows", json=sample_row_data)

        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data

    def test_create_row_invalid_type(self, client: FlaskClient, created_table: str):
        """Reject row with invalid data type."""
        response = client.post(f"/tables/{created_table}/rows", json={
            "data": {"name": "Alice", "age": "not a number", "active": True},
        })

        assert response.status_code == 400
        assert "age" in response.get_json().get("field", "") or "number" in response.get_json().get("error", "")

    def test_create_row_unknown_column(self, client: FlaskClient, created_table: str):
        """Reject row with unknown column."""
        response = client.post(f"/tables/{created_table}/rows", json={
            "data": {"name": "Alice", "unknown_col": "value"},
        })

        assert response.status_code == 400

    def test_create_row_table_not_found(self, client: FlaskClient):
        """Return 404 for non-existent table."""
        response = client.post("/tables/00000000-0000-0000-0000-000000000000/rows", json={
            "data": {"name": "Alice"},
        })

        assert response.status_code == 404


class TestGetRow:
    """Tests for GET /tables/<id>/rows/<row_id>."""

    def test_get_row_success(self, client: FlaskClient, created_row: tuple[str, str], sample_row_data: dict):
        """Successfully retrieve a row."""
        table_id, row_id = created_row
        response = client.get(f"/tables/{table_id}/rows/{row_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == row_id
        assert data["data"]["name"] == sample_row_data["data"]["name"]

    def test_get_row_not_found(self, client: FlaskClient, created_table: str):
        """Return 404 for non-existent row."""
        response = client.get(f"/tables/{created_table}/rows/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404


class TestUpdateRow:
    """Tests for PUT /tables/<id>/rows/<row_id>."""

    def test_update_row_success(self, client: FlaskClient, created_row: tuple[str, str]):
        """Successfully update a row."""
        table_id, row_id = created_row
        response = client.put(f"/tables/{table_id}/rows/{row_id}", json={
            "data": {"name": "Bob"},
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["name"] == "Bob"
        # Other fields should remain
        assert data["data"]["age"] == 30

    def test_update_row_invalid_type(self, client: FlaskClient, created_row: tuple[str, str]):
        """Reject update with invalid data type."""
        table_id, row_id = created_row
        response = client.put(f"/tables/{table_id}/rows/{row_id}", json={
            "data": {"age": "not a number"},
        })

        assert response.status_code == 400


class TestDeleteRow:
    """Tests for DELETE /tables/<id>/rows/<row_id>."""

    def test_delete_row_success(self, client: FlaskClient, created_row: tuple[str, str]):
        """Successfully delete a row."""
        table_id, row_id = created_row
        response = client.delete(f"/tables/{table_id}/rows/{row_id}")

        assert response.status_code == 204

        # Verify row is gone
        response = client.get(f"/tables/{table_id}/rows/{row_id}")
        assert response.status_code == 404


class TestListRows:
    """Tests for GET /tables/<id>/rows."""

    def test_list_rows_empty(self, client: FlaskClient, created_table: str):
        """Return empty list when no rows exist."""
        response = client.get(f"/tables/{created_table}/rows")

        assert response.status_code == 200
        data = response.get_json()
        assert data["rows"] == []
        assert data["total"] == 0

    def test_list_rows_with_data(self, client: FlaskClient, created_row: tuple[str, str]):
        """Return list of rows."""
        table_id, row_id = created_row
        response = client.get(f"/tables/{table_id}/rows")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["rows"]) == 1
        assert data["total"] == 1


class TestFilterRows:
    """Tests for filtering via GET /tables/<id>/rows?filter[col]=val."""

    def test_filter_by_string(self, client: FlaskClient, created_table: str):
        """Filter rows by string column."""
        # Create multiple rows
        client.post(f"/tables/{created_table}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}})
        client.post(f"/tables/{created_table}/rows", json={"data": {"name": "Bob", "age": 25, "active": True}})

        response = client.get(f"/tables/{created_table}/rows?filter[name]=Alice")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["rows"]) == 1
        assert data["rows"][0]["data"]["name"] == "Alice"

    def test_filter_by_number(self, client: FlaskClient, created_table: str):
        """Filter rows by number column."""
        client.post(f"/tables/{created_table}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}})
        client.post(f"/tables/{created_table}/rows", json={"data": {"name": "Bob", "age": 25, "active": True}})

        response = client.get(f"/tables/{created_table}/rows?filter[age]=30")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["rows"]) == 1
        assert data["rows"][0]["data"]["name"] == "Alice"

    def test_filter_by_boolean(self, client: FlaskClient, created_table: str):
        """Filter rows by boolean column."""
        client.post(f"/tables/{created_table}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}})
        client.post(f"/tables/{created_table}/rows", json={"data": {"name": "Bob", "age": 25, "active": False}})

        response = client.get(f"/tables/{created_table}/rows?filter[active]=false")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["rows"]) == 1
        assert data["rows"][0]["data"]["name"] == "Bob"

    def test_pagination(self, client: FlaskClient, created_table: str):
        """Test pagination with limit and offset."""
        for i in range(5):
            client.post(f"/tables/{created_table}/rows", json={"data": {"name": f"User{i}", "age": 20+i, "active": True}})

        response = client.get(f"/tables/{created_table}/rows?limit=2&offset=2")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data["rows"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 2

