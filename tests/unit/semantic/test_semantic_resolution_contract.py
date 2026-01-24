"""Contract tests for SemanticResolver producing valid SemanticResolution.

US-P4-008: These tests verify that the Semantic component (SemanticResolver)
produces SemanticResolution objects that fulfill the boundary contract.

Contract tests verify:
1. Resolution includes evaluation order (topological sort)
2. INCOMPLETE status when refs are missing
3. Resolution is serializable (round-trip to_dict/from_dict)
4. Resolution has resolved metrics with dependencies
5. Resolution has resolved dimensions with attributes
6. Resolution can be consumed by Query component
"""

from __future__ import annotations

from invariant.query.domain.value_objects.query_spec import (
    GroupBySpec,
    QuerySpec,
)
from invariant.semantic.domain.entities.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.semantic.domain.entities.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
)
from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog
from invariant.semantic.domain.services.resolver import SemanticResolver
from invariant.shared.contracts import (
    CatalogView,
    IdentityContext,
)
from invariant.shared.contracts.semantic_resolution import (
    RefType,
    ResolutionStatus,
    SemanticResolution,
)

# --- Test Fixtures ---


def make_simple_metric(name: str) -> Metric:
    """Create a simple aggregation metric for testing."""
    return Metric.create_simple_agg(
        name=name,
        dataset_name="test_dataset",
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def make_derived_metric(name: str, deps: list[str]) -> Metric:
    """Create a derived metric for testing."""
    return Metric.create_derived(
        name=name,
        expr=" + ".join(deps),
        deps=deps,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def make_dimension(name: str, attributes: list[str] | None = None) -> Dimension:
    """Create a dimension for testing."""
    if attributes is None:
        attributes = ["default"]
    attr_dict = {
        attr: DimensionAttribute(
            expr=attr,
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        for attr in attributes
    }
    return Dimension.create(name=name, attributes=attr_dict)


def make_catalog(
    metrics: list[Metric] | None = None,
    dimensions: list[Dimension] | None = None,
) -> SemanticCatalog:
    """Create a SemanticCatalog for testing."""
    return SemanticCatalog.create(
        metrics=metrics or [],
        dimensions=dimensions or [],
    )


def make_empty_catalog_view() -> CatalogView:
    """Create an empty CatalogView for testing."""
    return CatalogView(
        variables={},
        data_products={},
        datasets={},
    )


def make_empty_identity_context() -> IdentityContext:
    """Create an empty IdentityContext for testing."""
    return IdentityContext(
        concepts={},
        variable_semantics={},
        comparability_assertions={},
    )


# --- Contract Tests ---


class TestSemanticResolutionContract:
    """Contract tests for SemanticResolution production.

    These tests verify the boundary contract between the Semantic component
    and consuming components (e.g., Query, Validation).
    """

    def test_resolution_includes_evaluation_order(self) -> None:
        """SemanticResolution includes evaluation_order tuple.

        Contract: Resolution must include a topologically sorted evaluation
        order for metrics, enabling correct computation sequence.
        """
        # Create metrics with dependencies
        base_a = make_simple_metric("base_a")
        base_b = make_simple_metric("base_b")
        derived = make_derived_metric("derived", ["base_a", "base_b"])

        catalog = make_catalog(metrics=[base_a, base_b, derived])
        spec = QuerySpec(metrics=["derived"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # Contract: evaluation_order must be a tuple
        assert isinstance(result.evaluation_order, tuple)

        # Contract: evaluation_order must contain metric IDs
        assert len(result.evaluation_order) >= 1

        # Contract: dependencies must come before dependents
        base_a_idx = result.evaluation_order.index(str(base_a.id))
        base_b_idx = result.evaluation_order.index(str(base_b.id))
        derived_idx = result.evaluation_order.index(str(derived.id))

        assert base_a_idx < derived_idx
        assert base_b_idx < derived_idx

    def test_resolution_incomplete_when_refs_missing(self) -> None:
        """Resolution status is INCOMPLETE when references are missing.

        Contract: When requested metrics or dimensions cannot be resolved,
        the status must be INCOMPLETE (not ERROR) to allow partial execution.
        """
        # Create catalog with one metric
        known_metric = make_simple_metric("known_metric")
        catalog = make_catalog(metrics=[known_metric])

        # Request both known and unknown metrics
        spec = QuerySpec(metrics=["known_metric", "unknown_metric"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # Contract: status must be INCOMPLETE when refs are missing
        assert result.status == ResolutionStatus.INCOMPLETE

        # Contract: missing_refs must contain the unresolved reference
        assert len(result.missing_refs) == 1
        assert result.missing_refs[0].ref_name == "unknown_metric"
        assert result.missing_refs[0].ref_type == RefType.METRIC

        # Contract: can_proceed_partial must be True for INCOMPLETE
        assert result.can_proceed_partial is True

        # Contract: resolved metrics should still be present
        assert len(result.metrics) == 1
        assert result.metrics[0].name == "known_metric"

    def test_resolution_serializable_round_trip(self) -> None:
        """SemanticResolution survives to_dict() -> from_dict().

        Contract: Resolutions must be serializable for caching,
        transport, and audit purposes.
        """
        # Create a complex resolution scenario
        base_metric = make_simple_metric("population")
        derived_metric = make_derived_metric("growth_rate", ["population"])
        geo_dim = make_dimension("geography", ["code", "name", "level"])
        time_dim = make_dimension("time", ["year", "quarter"])

        catalog = make_catalog(
            metrics=[base_metric, derived_metric],
            dimensions=[geo_dim, time_dim],
        )

        spec = QuerySpec(
            metrics=["growth_rate", "population"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code"),
                GroupBySpec(dimension="time", attribute="year"),
            ],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        original = resolver.resolve(spec, catalog_view, identity_context)

        # Serialize and deserialize
        serialized = original.to_dict()
        restored = SemanticResolution.from_dict(serialized)

        # Contract: All fields must survive round-trip
        assert restored.status == original.status
        assert len(restored.metrics) == len(original.metrics)
        assert len(restored.dimensions) == len(original.dimensions)
        assert restored.evaluation_order == original.evaluation_order
        assert restored.missing_refs == original.missing_refs
        assert restored.ambiguous_refs == original.ambiguous_refs

        # Contract: Derived properties must be consistent
        assert restored.is_complete == original.is_complete
        assert restored.can_proceed_partial == original.can_proceed_partial

        # Contract: Metric details must match
        for orig, rest in zip(original.metrics, restored.metrics, strict=True):
            assert rest.name == orig.name
            assert rest.metric_id == orig.metric_id
            assert rest.dependencies == orig.dependencies

        # Contract: Dimension details must match
        for orig, rest in zip(original.dimensions, restored.dimensions, strict=True):
            assert rest.name == orig.name
            assert rest.dimension_id == orig.dimension_id
            assert rest.attributes == orig.attributes

    def test_resolution_has_resolved_metrics(self) -> None:
        """Resolution includes resolved metrics with dependencies.

        Contract: Each resolved metric must include its name, ID,
        and dependency list for downstream computation.
        """
        # Create metrics with dependencies
        base = make_simple_metric("base")
        derived = make_derived_metric("derived", ["base"])

        catalog = make_catalog(metrics=[base, derived])
        spec = QuerySpec(metrics=["derived", "base"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # Contract: metrics must be a tuple of ResolvedMetric
        assert isinstance(result.metrics, tuple)
        assert len(result.metrics) == 2

        # Find metrics by name
        metrics_by_name = {m.name: m for m in result.metrics}

        # Contract: base metric has no dependencies
        assert "base" in metrics_by_name
        base_resolved = metrics_by_name["base"]
        assert base_resolved.metric_id == str(base.id)
        assert base_resolved.dependencies == ()

        # Contract: derived metric has base as dependency
        assert "derived" in metrics_by_name
        derived_resolved = metrics_by_name["derived"]
        assert derived_resolved.metric_id == str(derived.id)
        assert "base" in derived_resolved.dependencies

    def test_resolution_has_resolved_dimensions(self) -> None:
        """Resolution includes resolved dimensions with attributes.

        Contract: Each resolved dimension must include its name, ID,
        and available attributes for grouping operations.
        """
        metric = make_simple_metric("count")
        geo_dim = make_dimension("geography", ["code", "name", "level", "parent"])
        time_dim = make_dimension("time", ["year", "quarter", "month"])

        catalog = make_catalog(
            metrics=[metric],
            dimensions=[geo_dim, time_dim],
        )

        spec = QuerySpec(
            metrics=["count"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code"),
                GroupBySpec(dimension="time", attribute="year"),
            ],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # Contract: dimensions must be a tuple of ResolvedDimension
        assert isinstance(result.dimensions, tuple)
        assert len(result.dimensions) == 2

        # Find dimensions by name
        dims_by_name = {d.name: d for d in result.dimensions}

        # Contract: geography dimension includes all attributes
        assert "geography" in dims_by_name
        geo_resolved = dims_by_name["geography"]
        assert geo_resolved.dimension_id == str(geo_dim.id)
        assert set(geo_resolved.attributes) == {"code", "name", "level", "parent"}

        # Contract: time dimension includes all attributes
        assert "time" in dims_by_name
        time_resolved = dims_by_name["time"]
        assert time_resolved.dimension_id == str(time_dim.id)
        assert set(time_resolved.attributes) == {"year", "quarter", "month"}


class TestSemanticResolutionConsumability:
    """Tests verifying SemanticResolution can be consumed by other components."""

    def test_resolution_can_be_used_for_query_planning(self) -> None:
        """SemanticResolution provides data needed for query planning.

        Contract: Resolution provides sufficient information for the Query
        component to build execution plans.
        """
        # Create a realistic scenario
        base_pop = make_simple_metric("population")
        base_gdp = make_simple_metric("gdp")
        gdp_per_capita = make_derived_metric("gdp_per_capita", ["gdp", "population"])
        geo_dim = make_dimension("geography", ["code", "name"])

        catalog = make_catalog(
            metrics=[base_pop, base_gdp, gdp_per_capita],
            dimensions=[geo_dim],
        )

        spec = QuerySpec(
            metrics=["gdp_per_capita"],
            group_by=[GroupBySpec(dimension="geography", attribute="code")],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        resolution = resolver.resolve(spec, catalog_view, identity_context)

        # Query planner needs to know which metrics to compute
        metric_ids_to_compute = set(resolution.evaluation_order)
        assert len(metric_ids_to_compute) >= 1  # At least the derived metric

        # Query planner needs to verify all metrics resolved
        assert resolution.is_complete
        assert resolution.status == ResolutionStatus.RESOLVED

        # Query planner needs dimension info for GROUP BY
        assert len(resolution.dimensions) == 1
        geo_dim_resolved = resolution.dimensions[0]
        assert geo_dim_resolved.name == "geography"
        assert "code" in geo_dim_resolved.attributes

        # Query planner can iterate metrics in evaluation order
        for metric_id in resolution.evaluation_order:
            # Each ID should correspond to a known metric
            assert isinstance(metric_id, str)
            assert len(metric_id) > 0

    def test_resolution_supports_partial_execution(self) -> None:
        """INCOMPLETE resolution supports partial query execution.

        Contract: When some refs are missing, resolution provides enough
        information to execute a partial query with resolved refs.
        """
        known = make_simple_metric("known")
        catalog = make_catalog(metrics=[known])

        # Request known metric + unknown dimension
        spec = QuerySpec(
            metrics=["known"],
            group_by=[GroupBySpec(dimension="unknown_dim", attribute="attr")],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        resolution = resolver.resolve(spec, catalog_view, identity_context)

        # Contract: Status is INCOMPLETE
        assert resolution.status == ResolutionStatus.INCOMPLETE

        # Contract: Partial execution is allowed
        assert resolution.can_proceed_partial is True

        # Contract: Resolved metric is available
        assert len(resolution.metrics) == 1
        assert resolution.metrics[0].name == "known"

        # Contract: Missing dimension is tracked
        assert len(resolution.missing_refs) == 1
        assert resolution.missing_refs[0].ref_name == "unknown_dim"
        assert resolution.missing_refs[0].ref_type == RefType.DIMENSION

    def test_resolution_serialization_is_json_compatible(self) -> None:
        """SemanticResolution.to_dict() produces JSON-serializable output.

        Contract: Resolution can be serialized to JSON for transport,
        caching, or audit logging.
        """
        import json

        metric = make_simple_metric("metric")
        dim = make_dimension("dim", ["a", "b"])
        catalog = make_catalog(metrics=[metric], dimensions=[dim])

        spec = QuerySpec(
            metrics=["metric", "unknown"],
            group_by=[GroupBySpec(dimension="dim", attribute="a")],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        resolution = resolver.resolve(spec, catalog_view, identity_context)

        # to_dict must produce JSON-serializable output
        serialized = resolution.to_dict()
        json_str = json.dumps(serialized)

        # Must round-trip through JSON
        parsed = json.loads(json_str)
        restored = SemanticResolution.from_dict(parsed)

        assert restored.status == resolution.status
        assert len(restored.metrics) == len(resolution.metrics)
        assert len(restored.missing_refs) == len(resolution.missing_refs)


class TestSemanticResolutionEdgeCases:
    """Tests for edge cases in SemanticResolution production."""

    def test_all_refs_missing_produces_incomplete(self) -> None:
        """Query with all unknown refs produces INCOMPLETE with empty resolved."""
        # Empty catalog - no metrics defined
        catalog = make_catalog()
        spec = QuerySpec(metrics=["unknown1", "unknown2"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # All refs missing -> INCOMPLETE
        assert result.status == ResolutionStatus.INCOMPLETE
        assert result.metrics == ()
        assert result.dimensions == ()
        assert len(result.missing_refs) == 2
        assert result.evaluation_order == ()
        # Partial execution still allowed (with nothing to execute)
        assert result.can_proceed_partial is True

    def test_duplicate_dimension_refs_deduplicated(self) -> None:
        """Duplicate dimension references in group_by are deduplicated."""
        metric = make_simple_metric("count")
        geo = make_dimension("geo", ["code", "name"])
        catalog = make_catalog(metrics=[metric], dimensions=[geo])

        # Same dimension used multiple times with different attributes
        spec = QuerySpec(
            metrics=["count"],
            group_by=[
                GroupBySpec(dimension="geo", attribute="code"),
                GroupBySpec(dimension="geo", attribute="name"),
            ],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # Contract: Dimension appears only once
        assert len(result.dimensions) == 1
        assert result.dimensions[0].name == "geo"

    def test_cyclic_dependencies_produce_error_status(self) -> None:
        """Cyclic metric dependencies produce ERROR status."""
        # Create cycle: a -> b -> a
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])
        catalog = make_catalog(metrics=[a, b])

        spec = QuerySpec(metrics=["a"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # Contract: Status is ERROR for cycles
        assert result.status == ResolutionStatus.ERROR

        # Contract: Cannot proceed with ERROR
        assert result.can_proceed_partial is False
        assert result.is_complete is False
