"""Routes for the Data Dictionary web application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import abort, current_app, render_template, request

from invariant.domain.model.metric import (
    DerivedSpec,
    MetricKind,
    RatioSpec,
    SimpleAggSpec,
)

if TYPE_CHECKING:
    from flask import Flask

    from invariant.application.ports.semantic_asset_store import SemanticAssetStore


def get_asset_store() -> SemanticAssetStore:
    """Get the asset store from the current app config."""
    return current_app.config["ASSET_STORE"]


def register_routes(app: Flask) -> None:
    """Register all routes with the Flask application.

    Args:
        app: The Flask application to register routes with.
    """

    @app.route("/")
    def index():
        """Render the dashboard/index page."""
        catalog = get_asset_store().load_catalog()

        return render_template(
            "index.html",
            dataset_count=len(catalog.datasets),
            metric_count=len(catalog.metrics),
            dimension_count=len(catalog.dimensions),
        )

    @app.route("/datasets")
    def datasets_list():
        """Render the datasets list page."""
        catalog = get_asset_store().load_catalog()
        search_query = request.args.get("q", "").lower()

        datasets = catalog.datasets
        if search_query:
            datasets = [ds for ds in datasets if search_query in ds.name.lower()]

        return render_template(
            "datasets.html",
            datasets=datasets,
            search_query=request.args.get("q", ""),
        )

    @app.route("/datasets/<name>")
    def dataset_detail(name: str):
        """Render the dataset detail page."""
        store = get_asset_store()
        dataset = store.get_dataset(name)

        if dataset is None:
            abort(404)

        catalog = store.load_catalog()

        # Find metrics associated with this dataset
        associated_metrics = [
            m
            for m in catalog.metrics
            if (isinstance(m.spec, SimpleAggSpec) and m.spec.dataset_name == name)
        ]

        return render_template(
            "dataset_detail.html",
            dataset=dataset,
            associated_metrics=associated_metrics,
        )

    @app.route("/indicators")
    def indicators_list():
        """Render the indicators list page."""
        catalog = get_asset_store().load_catalog()
        search_query = request.args.get("q", "").lower()
        tag_filter = request.args.get("tag", "")
        kind_filter = request.args.get("kind", "")

        metrics = list(catalog.metrics)

        # Apply text search
        if search_query:
            metrics = [
                m
                for m in metrics
                if (
                    search_query in m.name.lower()
                    or (m.description and search_query in m.description.lower())
                )
            ]

        # Apply tag filter
        if tag_filter:
            tag_lower = tag_filter.lower()
            metrics = [
                m for m in metrics if any(tag_lower == t.lower() for t in m.tags)
            ]

        # Apply kind filter
        if kind_filter:
            try:
                kind = MetricKind(kind_filter)
                metrics = [m for m in metrics if m.kind == kind]
            except ValueError:
                pass

        # Collect all unique tags for filter chips
        all_tags: set[str] = set()
        for m in catalog.metrics:
            all_tags.update(m.tags)

        return render_template(
            "indicators.html",
            metrics=metrics,
            search_query=request.args.get("q", ""),
            tag_filter=tag_filter,
            kind_filter=kind_filter,
            all_tags=sorted(all_tags),
            metric_kinds=[k.value for k in MetricKind],
        )

    @app.route("/indicators/<name>")
    def indicator_detail(name: str):
        """Render the indicator detail page."""
        store = get_asset_store()
        metric = store.get_metric(name)

        if metric is None:
            abort(404)

        # Get dependency metrics for RATIO/DERIVED
        dependencies: list[tuple[str, bool]] = []  # (name, exists)
        if isinstance(metric.spec, RatioSpec):
            dependencies.append(
                (
                    metric.spec.numerator,
                    store.get_metric(metric.spec.numerator) is not None,
                )
            )
            dependencies.append(
                (
                    metric.spec.denominator,
                    store.get_metric(metric.spec.denominator) is not None,
                )
            )
        elif isinstance(metric.spec, DerivedSpec):
            for dep in metric.spec.deps:
                dependencies.append((dep, store.get_metric(dep) is not None))

        return render_template(
            "indicator_detail.html",
            metric=metric,
            dependencies=dependencies,
        )

    @app.errorhandler(404)
    def not_found(error):
        """Render the 404 error page."""
        return render_template("404.html"), 404
