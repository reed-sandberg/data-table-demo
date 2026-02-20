"""Application configuration."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    database_path: str = os.environ.get("DATABASE_PATH", "data_tables.db")
    debug: bool = os.environ.get("FLASK_DEBUG", "0") == "1"
    max_columns_per_table: int = 500


config = Config()
