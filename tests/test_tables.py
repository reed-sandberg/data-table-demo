"""Tests for table management endpoints."""

from flask.testing import FlaskClient


class TestCreateTable:
    """Tests for POST /tables."""

    def test_create_table_success(self, client: FlaskClient, sample_table_data: dict):
        """Successfully create a table with valid schema."""
        response = client.post("/tables", json=sample_table_data)

        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert len(data["id"]) == 36  # UUID format

    def test_create_table_duplicate_name(self, client: FlaskClient, sample_table_data: dict):
        """Reject duplicate table names."""
        client.post("/tables", json=sample_table_data)
        response = client.post("/tables", json=sample_table_data)

        assert response.status_code == 409
        assert "already exists" in response.get_json()["error"]

    def test_create_table_invalid_column_type(self, client: FlaskClient):
        """Reject invalid column types."""
        response = client.post(
            "/tables",
            json={
                "name": "test",
                "columns": [{"name": "col1", "type": "invalid"}],
            },
        )

        assert response.status_code == 400

    def test_create_table_duplicate_column_names(self, client: FlaskClient):
        """Reject duplicate column names within a table."""
        response = client.post(
            "/tables",
            json={
                "name": "test",
                "columns": [
                    {"name": "col1", "type": "string"},
                    {"name": "col1", "type": "number"},
                ],
            },
        )

        assert response.status_code == 400

    def test_create_table_empty_columns(self, client: FlaskClient):
        """Reject tables with no columns."""
        response = client.post(
            "/tables",
            json={
                "name": "test",
                "columns": [],
            },
        )

        assert response.status_code == 400

    def test_create_table_max_columns_exceeded(self, client: FlaskClient):
        """Reject tables with more than 500 columns."""
        # Create exactly 501 columns to exceed the limit
        columns = [{"name": f"col_{i}", "type": "string"} for i in range(501)]
        response = client.post(
            "/tables",
            json={
                "name": "too_many_columns",
                "columns": columns,
            },
        )

        assert response.status_code == 400
        # Error comes from Pydantic max_length validation on the columns field
        data = response.get_json()
        assert "error" in data

    def test_create_table_at_max_columns(self, client: FlaskClient):
        """Accept table with exactly 500 columns (the limit)."""
        columns = [{"name": f"col_{i}", "type": "string"} for i in range(500)]
        response = client.post(
            "/tables",
            json={
                "name": "max_columns_table",
                "columns": columns,
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data


class TestGetTable:
    """Tests for GET /tables/<id>."""

    def test_get_table_success(self, client: FlaskClient, created_table: str, sample_table_data: dict):
        """Successfully retrieve table details."""
        response = client.get(f"/tables/{created_table}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == created_table
        assert data["name"] == sample_table_data["name"]
        assert len(data["columns"]) == len(sample_table_data["columns"])

    def test_get_table_not_found(self, client: FlaskClient):
        """Return 404 for non-existent table."""
        response = client.get("/tables/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404


class TestListTables:
    """Tests for GET /tables."""

    def test_list_tables_empty(self, client: FlaskClient):
        """Return empty list when no tables exist."""
        response = client.get("/tables")

        assert response.status_code == 200
        assert response.get_json() == []

    def test_list_tables_with_data(self, client: FlaskClient, created_table: str):
        """Return list of tables."""
        response = client.get("/tables")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["id"] == created_table


class TestDeleteTable:
    """Tests for DELETE /tables/<id>."""

    def test_delete_table_success(self, client: FlaskClient, created_table: str):
        """Successfully delete a table."""
        response = client.delete(f"/tables/{created_table}")

        assert response.status_code == 204

        # Verify table is gone
        response = client.get(f"/tables/{created_table}")
        assert response.status_code == 404

    def test_delete_table_not_found(self, client: FlaskClient):
        """Return 404 for non-existent table."""
        response = client.delete("/tables/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404


class TestUpdateSchema:
    """Tests for PATCH /tables/<id>/schema."""

    def test_add_column(self, client: FlaskClient, created_table: str):
        """Successfully add a new column."""
        response = client.patch(
            f"/tables/{created_table}/schema",
            json={
                "add_columns": [{"name": "email", "type": "string"}],
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        column_names = [c["name"] for c in data["columns"]]
        assert "email" in column_names

    def test_remove_column(self, client: FlaskClient, created_table: str):
        """Successfully remove a column."""
        response = client.patch(
            f"/tables/{created_table}/schema",
            json={
                "remove_columns": ["age"],
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        column_names = [c["name"] for c in data["columns"]]
        assert "age" not in column_names

    def test_remove_nonexistent_column(self, client: FlaskClient, created_table: str):
        """Reject removing non-existent column."""
        response = client.patch(
            f"/tables/{created_table}/schema",
            json={
                "remove_columns": ["nonexistent"],
            },
        )

        assert response.status_code == 400

    def test_add_duplicate_column(self, client: FlaskClient, created_table: str):
        """Reject adding column with existing name."""
        response = client.patch(
            f"/tables/{created_table}/schema",
            json={
                "add_columns": [{"name": "name", "type": "string"}],
            },
        )

        assert response.status_code == 400

    def test_remove_column_updates_existing_rows(self, client: FlaskClient, created_table: str):
        """Removing a column should update existing row data to remove that field."""
        # Create a row with all columns
        row_response = client.post(
            f"/tables/{created_table}/rows", json={"data": {"name": "Alice", "age": 30, "active": True}}
        )
        assert row_response.status_code == 201
        row_id = row_response.get_json()["id"]

        # Remove the 'age' column
        schema_response = client.patch(
            f"/tables/{created_table}/schema",
            json={
                "remove_columns": ["age"],
            },
        )
        assert schema_response.status_code == 200

        # Verify the row no longer has the 'age' field
        get_response = client.get(f"/tables/{created_table}/rows/{row_id}")
        assert get_response.status_code == 200
        row_data = get_response.get_json()["data"]
        assert "age" not in row_data
        assert row_data["name"] == "Alice"
        assert row_data["active"] is True
