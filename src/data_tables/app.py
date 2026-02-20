"""Flask application factory."""

from __future__ import annotations

from typing import Optional

from flask import Flask, jsonify

from .database import close_db, init_db
from .routes import rows_bp, tables_bp


def create_app(test_config: Optional[dict] = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        test_config: Optional configuration dict for testing.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Default configuration
    app.config.from_mapping(
        DATABASE_PATH="data_tables.db",
    )

    # Override with test config if provided
    if test_config:
        app.config.update(test_config)

    # Register teardown to close DB connections
    app.teardown_appcontext(close_db)

    # Initialize database on first request
    with app.app_context():
        init_db()

    # Register blueprints
    app.register_blueprint(tables_bp)
    app.register_blueprint(rows_bp)

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "version": "0.1.0"}), 200

    # Root endpoint with API info
    @app.route("/")
    def index():
        return jsonify({
            "name": "Data Tables API",
            "version": "0.1.0",
            "endpoints": {
                "tables": {
                    "POST /tables": "Create a new table",
                    "GET /tables": "List all tables",
                    "GET /tables/<id>": "Get table details",
                    "DELETE /tables/<id>": "Delete a table",
                    "PATCH /tables/<id>/schema": "Update table schema",
                },
                "rows": {
                    "GET /tables/<id>/rows": "List rows (supports ?filter[col]=val)",
                    "POST /tables/<id>/rows": "Create a row",
                    "GET /tables/<id>/rows/<row_id>": "Get a row",
                    "PUT /tables/<id>/rows/<row_id>": "Update a row",
                    "DELETE /tables/<id>/rows/<row_id>": "Delete a row",
                },
            },
        }), 200

    return app


# Create default app instance for flask CLI
app = create_app()

