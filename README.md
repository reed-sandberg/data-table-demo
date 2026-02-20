# Data Tables API

A flexible REST API service for creating and managing dynamic tables with custom schemas. Users can define tables with typed columns, modify schemas on the fly, and perform CRUD operations on rows with type validation.

## Features

- **Dynamic Schema**: Create tables with custom columns (string, number, boolean types)
- **Schema Evolution**: Add or remove columns from existing tables
- **Type Validation**: Automatic validation of row data against column types
- **Filtering**: Query rows with column-based filters (`?filter[name]=Alice`)
- **Pagination**: Limit and offset support for row listings
- **JSONB Storage**: Efficient binary JSON storage using SQLite 3.45+

## Tech Stack

- **Python 3.11+** with type hints
- **Flask 3.x** - Web framework
- **Pydantic 2.x** - Request/response validation
- **SQLite 3.45+** - Database with JSONB support
- **Docker** - Containerization

## Quick Start

### Using Docker (Recommended)

```bash
# Build and run
make docker-build
make docker-start

# Health check
curl http://localhost:5000/health

# Stop the service
make docker-stop
```

### Local Development

Requires SQLite 3.45+ for JSONB support. Check your version:

```bash
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
```

If your SQLite is older, use Docker or install a newer Python via pyenv.

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
make install

# Run the development server
make run

# Run tests
make test
```

## API Reference

### Health Check

```
GET /health
```

**Response** `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### Tables

#### Create Table

```
POST /tables
```

**Request Body**
```json
{
  "name": "users",
  "columns": [
    {"name": "email", "type": "string"},
    {"name": "age", "type": "number"},
    {"name": "active", "type": "boolean"}
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique table name |
| `columns` | array | Yes | List of column definitions (min: 1) |
| `columns[].name` | string | Yes | Column name (unique within table) |
| `columns[].type` | string | Yes | One of: `string`, `number`, `boolean` |

**Response** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors**
- `400 Bad Request` - Invalid column type or duplicate column names
- `409 Conflict` - Table name already exists

---

#### List Tables

```
GET /tables
```

**Response** `200 OK`
```json
{
  "tables": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "users",
      "columns": [
        {"name": "email", "type": "string"},
        {"name": "age", "type": "number"}
      ],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### Get Table

```
GET /tables/{table_id}
```

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "users",
  "columns": [
    {"name": "email", "type": "string"},
    {"name": "age", "type": "number"}
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors**
- `404 Not Found` - Table does not exist

---

#### Delete Table

```
DELETE /tables/{table_id}
```

**Response** `204 No Content`

**Errors**
- `404 Not Found` - Table does not exist

---

#### Update Schema

```
PATCH /tables/{table_id}/schema
```

**Request Body** - Add columns
```json
{
  "add_columns": [
    {"name": "phone", "type": "string"}
  ]
}
```

**Request Body** - Remove columns
```json
{
  "remove_columns": ["phone"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `add_columns` | array | No | Columns to add |
| `remove_columns` | array | No | Column names to remove |

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "users",
  "columns": [
    {"name": "email", "type": "string"},
    {"name": "age", "type": "number"},
    {"name": "phone", "type": "string"}
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors**
- `404 Not Found` - Table does not exist
- `400 Bad Request` - Column already exists or column to remove not found

---

### Rows

#### Create Row

```
POST /tables/{table_id}/rows
```

**Request Body**
```json
{
  "data": {
    "email": "alice@example.com",
    "age": 30,
    "active": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | object | Yes | Key-value pairs matching table schema |

**Response** `201 Created`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "table_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "email": "alice@example.com",
    "age": 30,
    "active": true
  },
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Errors**
- `404 Not Found` - Table does not exist
- `400 Bad Request` - Type validation failed or unknown column

---

#### List Rows

```
GET /tables/{table_id}/rows
```

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum rows to return |
| `offset` | integer | 0 | Number of rows to skip |
| `filter[column]` | string | - | Filter by column value |

**Example with filtering**
```
GET /tables/{table_id}/rows?filter[age]=30&filter[active]=true&limit=10
```

**Response** `200 OK`
```json
{
  "rows": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "table_id": "550e8400-e29b-41d4-a716-446655440000",
      "data": {
        "email": "alice@example.com",
        "age": 30,
        "active": true
      },
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

---

#### Get Row

```
GET /tables/{table_id}/rows/{row_id}
```

**Response** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "table_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "email": "alice@example.com",
    "age": 30,
    "active": true
  },
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**Errors**
- `404 Not Found` - Table or row does not exist

---

#### Update Row

```
PUT /tables/{table_id}/rows/{row_id}
```

**Request Body**
```json
{
  "data": {
    "email": "alice.updated@example.com",
    "age": 31,
    "active": false
  }
}
```

**Response** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "table_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "email": "alice.updated@example.com",
    "age": 31,
    "active": false
  },
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

**Errors**
- `404 Not Found` - Table or row does not exist
- `400 Bad Request` - Type validation failed

---

#### Delete Row

```
DELETE /tables/{table_id}/rows/{row_id}
```

**Response** `204 No Content`

**Errors**
- `404 Not Found` - Table or row does not exist

---

## Project Structure

```
├── src/data_tables/
│   ├── app.py              # Flask application factory
│   ├── config.py           # Configuration settings
│   ├── database.py         # SQLite connection & transactions
│   ├── schema.sql          # Database DDL
│   ├── models/             # Pydantic request/response models
│   │   ├── column.py       # Column type definitions
│   │   ├── table.py        # Table schemas
│   │   └── row.py          # Row schemas
│   ├── routes/             # API endpoint handlers
│   │   ├── tables.py       # /tables endpoints
│   │   └── rows.py         # /tables/{id}/rows endpoints
│   └── services/           # Business logic layer
│       ├── table_service.py
│       ├── row_service.py
│       └── validation.py   # Type validation
├── tests/                  # Pytest test suite
├── scripts/demo.sh         # Interactive API demo
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## Design Decisions

### JSON Storage vs Dynamic SQL Tables

Row data is stored as JSON in a single `rows` table rather than creating separate SQL tables for each user-defined table. This approach was chosen because:

- **Schema flexibility is the core feature** - Users can add/remove columns without DDL migrations
- **Simpler implementation** - No dynamic SQL generation or table management
- **Consistent query patterns** - All row operations use the same code paths
- **SQLite JSONB** - Binary JSON provides efficient storage and querying via `json_extract()`

Trade-off: Complex queries across columns require JSON function calls, which may be slower than native SQL columns for large datasets.

### JSONB for Storage

SQLite 3.45+ JSONB is used for row data storage:
- ~2x faster reads compared to TEXT JSON
- 5-10% smaller storage footprint
- Full compatibility with `json_extract()` for filtering

Note: Requires SQLite 3.45+ (January 2024). Docker image includes a compatible version.

### Service Layer Architecture

Business logic is separated into service classes (`TableService`, `RowService`, `ValidationService`) rather than being embedded in route handlers:

- **Testability** - Services can be unit tested independently
- **Reusability** - Logic can be shared across different interfaces
- **Separation of concerns** - Routes handle HTTP, services handle business rules

### Transaction Management

Database transactions use a context manager pattern:

```python
with transaction(conn):
    # All operations here are atomic
    conn.execute(...)
    conn.execute(...)
```

This ensures atomicity for multi-statement operations like creating a table with its columns.

### Type Validation Strategy

Validation happens at two levels:
1. **Pydantic models** - Request structure validation (required fields, types)
2. **ValidationService** - Row data validation against table schema (column types)

This provides clear error messages indicating whether the request format is wrong vs. the data doesn't match the schema.

---

## Limitations

- **Single-node only** - SQLite is not suitable for distributed deployments
- **No authentication** - All endpoints are publicly accessible
- **Basic filtering** - Only exact match equality filters; no operators like `>`, `<`, `LIKE`
- **No relationships** - Cannot define foreign keys between user-defined tables
- **No indexing** - Cannot create indexes on JSON columns (would require expression indexes)
- **Schema validation on write only** - Existing rows aren't validated when columns are removed
- **No column renaming** - Schema updates only support add/remove, not rename
- **No default values** - Columns cannot have default values for new rows

---

## Future Improvements

- [ ] **Authentication & Authorization** - JWT tokens, API keys, per-table permissions
- [ ] **Multi-tenant architecture** - Isolate each customer's data with dedicated SQL tables per user-defined table. This provides natural partitioning for improved query performance, better support for large datasets, and stronger data isolation. Each tenant's "users" table becomes a separate `tenant_123_users` SQL table with native columns instead of JSON.
- [ ] **Advanced filtering** - Comparison operators, `LIKE`, `IN`, `IS NULL`
- [ ] **Sorting** - `?sort=column&order=asc|desc`
- [ ] **Full-text search** - SQLite FTS5 integration for string columns
- [ ] **Column constraints** - Required fields, unique values, min/max for numbers
- [ ] **Default values** - Specify defaults when adding columns
- [ ] **Bulk operations** - Create/update multiple rows in a single request
- [ ] **Webhooks** - Notify external services on data changes
- [ ] **Export/Import** - CSV, JSON export and bulk import
- [ ] **PostgreSQL backend** - Swap SQLite for PostgreSQL for production scale
- [ ] **OpenAPI spec** - Auto-generated API documentation with Swagger UI
- [ ] **Rate limiting** - Protect against abuse

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies in dev mode |
| `make run` | Run Flask development server |
| `make test` | Run test suite |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Check code style (ruff + black) |
| `make format` | Auto-format code |
| `make clean` | Remove cache files and databases |
| `make docker-build` | Build Docker image |
| `make docker-start` | Start container (detached) |
| `make docker-stop` | Stop and remove container |
| `make docker-test` | Run tests inside Docker |
| `make docker-run` | Run via docker-compose |
| `make docker-down` | Stop docker-compose |

