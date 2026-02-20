-- Data Tables API Schema
-- Using JSONB for flexible row storage

-- Enable foreign keys (must be done per connection in SQLite)
PRAGMA foreign_keys = ON;

-- Tables metadata
CREATE TABLE IF NOT EXISTS tables (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Column definitions (schema registry)
CREATE TABLE IF NOT EXISTS columns (
    id TEXT PRIMARY KEY,
    table_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('string', 'number', 'boolean')),
    position INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(table_id, name),
    UNIQUE(table_id, position),  -- Prevents race conditions in concurrent schema updates
    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE
);

-- Row data stored as JSONB
CREATE TABLE IF NOT EXISTS rows (
    id TEXT PRIMARY KEY,
    table_id TEXT NOT NULL,
    data BLOB NOT NULL,  -- JSONB format
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_columns_table_id ON columns(table_id);
CREATE INDEX IF NOT EXISTS idx_rows_table_id ON rows(table_id);

