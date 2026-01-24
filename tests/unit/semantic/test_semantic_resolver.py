"""Tests for SemanticResolver domain service."""

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


class TestSemanticResolverReturnsResolution:
    """Test that SemanticResolver returns SemanticResolution."""

    def test_resolver_returns_semantic_resolution(self) -> None:
        """Resolver returns SemanticResolution instance."""
        metric = make_simple_metric("population")
        catalog = make_catalog(metrics=[metric])
        spec = QuerySpec(metrics=["population"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert isinstance(result, SemanticResolution)

    def test_resolver_returns_resolved_status_for_valid_query(self) -> None:
        """Resolver returns RESOLVED status when all refs are found."""
        metric = make_simple_metric("population")
        catalog = make_catalog(metrics=[metric])
        spec = QuerySpec(metrics=["population"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert result.status == ResolutionStatus.RESOLVED


class TestSemanticResolverResolvesMetrics:
    """Test that SemanticResolver resolves metric references."""

    def test_resolver_resolves_single_metric(self) -> None:
        """Resolver resolves a single metric reference."""
        metric = make_simple_metric("population")
        catalog = make_catalog(metrics=[metric])
        spec = QuerySpec(metrics=["population"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert len(result.metrics) == 1
        assert result.metrics[0].name == "population"
        assert result.metrics[0].metric_id == str(metric.id)

    def test_resolver_resolves_multiple_metrics(self) -> None:
        """Resolver resolves multiple metric references."""
        pop = make_simple_metric("population")
        gdp = make_simple_metric("gdp")
        catalog = make_catalog(metrics=[pop, gdp])
        spec = QuerySpec(metrics=["population", "gdp"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert len(result.metrics) == 2
        metric_names = {m.name for m in result.metrics}
        assert metric_names == {"population", "gdp"}

    def test_resolver_includes_metric_dependencies(self) -> None:
        """Resolver includes dependencies in ResolvedMetric."""
        base_a = make_simple_metric("base_a")
        base_b = make_simple_metric("base_b")
        derived = make_derived_metric("derived", ["base_a", "base_b"])
        catalog = make_catalog(metrics=[base_a, base_b, derived])
        spec = QuerySpec(metrics=["derived"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # Find the derived metric in results
        derived_resolved = next(m for m in result.metrics if m.name == "derived")
        assert set(derived_resolved.dependencies) == {"base_a", "base_b"}


class TestSemanticResolverResolvesDimensions:
    """Test that SemanticResolver resolves dimension references."""

    def test_resolver_resolves_dimensions_from_group_by(self) -> None:
        """Resolver resolves dimension references from group_by."""
        metric = make_simple_metric("population")
        dim = make_dimension("geography", ["province", "municipality"])
        catalog = make_catalog(metrics=[metric], dimensions=[dim])
        spec = QuerySpec(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="geography", attribute="province")],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert len(result.dimensions) == 1
        assert result.dimensions[0].name == "geography"
        assert result.dimensions[0].dimension_id == str(dim.id)

    def test_resolver_includes_dimension_attributes(self) -> None:
        """Resolver includes available attributes in ResolvedDimension."""
        metric = make_simple_metric("population")
        dim = make_dimension("geography", ["province", "municipality", "ward"])
        catalog = make_catalog(metrics=[metric], dimensions=[dim])
        spec = QuerySpec(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="geography", attribute="province")],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        geo_dim = result.dimensions[0]
        assert set(geo_dim.attributes) == {"province", "municipality", "ward"}


class TestSemanticResolverEvaluationOrder:
    """Test that SemanticResolver includes evaluation order."""

    def test_resolver_includes_evaluation_order(self) -> None:
        """Resolution includes topological evaluation order."""
        metric = make_simple_metric("population")
        catalog = make_catalog(metrics=[metric])
        spec = QuerySpec(metrics=["population"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert len(result.evaluation_order) == 1
        assert str(metric.id) in result.evaluation_order

    def test_resolver_evaluation_order_respects_dependencies(self) -> None:
        """Evaluation order puts dependencies before dependents."""
        base = make_simple_metric("base")
        derived = make_derived_metric("derived", ["base"])
        catalog = make_catalog(metrics=[base, derived])
        spec = QuerySpec(metrics=["derived"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # base must appear before derived in evaluation order
        base_idx = result.evaluation_order.index(str(base.id))
        derived_idx = result.evaluation_order.index(str(derived.id))
        assert base_idx < derived_idx

    def test_resolver_evaluation_order_for_complex_deps(self) -> None:
        """Evaluation order handles complex dependency chains."""
        # a -> b -> c, a -> c (diamond pattern)
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["a", "b"])
        catalog = make_catalog(metrics=[a, b, c])
        spec = QuerySpec(metrics=["c"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        # a must come before b and c
        a_idx = result.evaluation_order.index(str(a.id))
        b_idx = result.evaluation_order.index(str(b.id))
        c_idx = result.evaluation_order.index(str(c.id))
        assert a_idx < b_idx
        assert a_idx < c_idx
        assert b_idx < c_idx


class TestSemanticResolverMissingRefs:
    """Test that SemanticResolver handles missing references."""

    def test_resolver_returns_incomplete_for_missing_metric(self) -> None:
        """Returns INCOMPLETE status when metrics are missing."""
        # Empty catalog - no metrics defined
        catalog = make_catalog()
        spec = QuerySpec(metrics=["unknown_metric"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert result.status == ResolutionStatus.INCOMPLETE

    def test_resolver_includes_missing_metric_refs(self) -> None:
        """Resolver tracks missing metric references."""
        catalog = make_catalog()
        spec = QuerySpec(metrics=["unknown_metric"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert len(result.missing_refs) == 1
        assert result.missing_refs[0].ref_name == "unknown_metric"
        assert result.missing_refs[0].ref_type == RefType.METRIC

    def test_resolver_returns_incomplete_for_missing_dimension(self) -> None:
        """Returns INCOMPLETE status when dimensions are missing."""
        metric = make_simple_metric("population")
        catalog = make_catalog(metrics=[metric])  # No dimensions
        spec = QuerySpec(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="unknown_dim", attribute="attr")],
        )
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert result.status == ResolutionStatus.INCOMPLETE
        assert len(result.missing_refs) == 1
        assert result.missing_refs[0].ref_name == "unknown_dim"
        assert result.missing_refs[0].ref_type == RefType.DIMENSION

    def test_resolver_can_proceed_partial_with_incomplete(self) -> None:
        """INCOMPLETE resolution can_proceed_partial is True."""
        metric = make_simple_metric("population")
        catalog = make_catalog(metrics=[metric])
        spec = QuerySpec(metrics=["population", "unknown"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert result.status == ResolutionStatus.INCOMPLETE
        assert result.can_proceed_partial is True


class TestSemanticResolverError:
    """Test that SemanticResolver handles errors."""

    def test_resolver_returns_error_for_cyclic_dependencies(self) -> None:
        """Returns ERROR status for cyclic dependencies."""
        # Create a cycle: a -> b -> a
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])
        catalog = make_catalog(metrics=[a, b])
        spec = QuerySpec(metrics=["a"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert result.status == ResolutionStatus.ERROR

    def test_resolver_error_cannot_proceed(self) -> None:
        """ERROR resolution can_proceed_partial is False."""
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])
        catalog = make_catalog(metrics=[a, b])
        spec = QuerySpec(metrics=["a"])
        catalog_view = make_empty_catalog_view()
        identity_context = make_empty_identity_context()

        resolver = SemanticResolver(catalog)
        result = resolver.resolve(spec, catalog_view, identity_context)

        assert result.status == ResolutionStatus.ERROR
        assert result.can_proceed_partial is False


class TestSemanticResolverImportable:
    """Test that SemanticResolver is importable from expected locations."""

    def test_resolver_importable_from_services(self) -> None:
        """SemanticResolver is importable from semantic.domain.services."""
        from invariant.semantic.domain.services import SemanticResolver as SR

        assert SR is SemanticResolver
