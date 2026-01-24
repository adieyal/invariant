"""Flask application factory for the Data Dictionary web interface."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Flask

if TYPE_CHECKING:
    from invariant.application.ports.semantic_asset_store import SemanticAssetStore


def create_app(asset_store: SemanticAssetStore) -> Flask:
    """Create and configure the Flask application.

    Args:
        asset_store: The semantic asset store to use for loading catalog data.

    Returns:
        Configured Flask application instance.
    """
    # Get the package directory for templates and static files
    package_dir = Path(__file__).parent

    app = Flask(
        __name__,
        template_folder=str(package_dir / "templates"),
        static_folder=str(package_dir / "static"),
    )

    # Store asset_store in app config for access in routes
    app.config["ASSET_STORE"] = asset_store

    # Register routes
    from invariant_contrib.datadictionary_web.routes import register_routes

    register_routes(app)

    return app
