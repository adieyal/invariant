"""Tests for SemanticCatalog aggregate."""

from invariant.domain.model.comparability_rules import (
    ComparabilityPolicy,
    ComparabilityRules,
)
from invariant.domain.model.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.domain.model.geo_hierarchy import GeoHierarchy
from invariant.domain.model.ids import ComparabilityRuleId
from invariant.domain.model.materialization import (
    Materialization,
    MaterializationGrain,
    MaterializationSource,
    RefreshConfig,
    RefreshStrategy,
    SourceType,
    StorageConfig,
)
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
)
from invariant.domain.model.semantic_catalog import SemanticCatalog
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
)

# Fixtures for test data


def make_dataset(name: str) -> SemanticDataset:
    """Create a simple dataset for testing."""
    return SemanticDataset.create(
        name=name,
        physical_ref=PhysicalRef(schema="public", table=name),
        kind=DatasetKind.FACT,
        grain_keys=GrainKeys(other=["id"]),
    )


def make_dimension(name: str) -> Dimension:
    """Create a simple dimension for testing."""
    return Dimension.create(
        name=name,
        attributes={
            "code": DimensionAttribute(
                expr="code",
                data_type=DataType.STRING,
                semantic_type=SemanticType.CATEGORY,
            )
        },
    )


def make_geo_hierarchy(name: str) -> GeoHierarchy:
    """Create a simple geo hierarchy for testing."""
    return GeoHierarchy.create(
        name=name,
        levels=["country", "province", "municipality"],
    )


def make_simple_metric(name: str, dataset_name: str) -> Metric:
    """Create a simple aggregation metric for testing."""
    return Metric.create_simple_agg(
        name=name,
        dataset_name=dataset_name,
        expr="value",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def make_derived_metric(name: str, deps: list[str]) -> Metric:
    """Create a derived metric for testing."""
    return Metric.create_derived(
        name=name,
        expr="dep1 + dep2",
        deps=deps,
        additivity=Additivity(type=AdditivityType.NON_ADDITIVE),
    )


def make_ratio_metric(name: str, numerator: str, denominator: str) -> Metric:
    """Create a ratio metric for testing."""
    return Metric.create_ratio(
        name=name,
        numerator=numerator,
        denominator=denominator,
        additivity=Additivity(type=AdditivityType.NON_ADDITIVE),
    )


def make_materialization(
    name: str, dataset_name: str, metrics: list[str]
) -> Materialization:
    """Create a materialization for testing."""
    return Materialization.create(
        name=name,
        source=MaterializationSource(type=SourceType.PROFILE),
        dataset_name=dataset_name,
        grain=MaterializationGrain(),
        metrics=metrics,
        refresh=RefreshConfig(strategy=RefreshStrategy.MANUAL),
        storage=StorageConfig(schema="public", table=f"{name}_mat"),
    )


def make_comparability_rules() -> ComparabilityRules:
    """Create comparability rules for testing."""
    return ComparabilityRules(
        id=ComparabilityRuleId.create(),
        default_policy=ComparabilityPolicy.WARN,
    )


class TestSemanticCatalogConstruction:
    """Tests for SemanticCatalog construction."""

    def test_create_empty_catalog(self) -> None:
        catalog = SemanticCatalog.create()
        assert catalog.datasets == []
        assert catalog.dimensions == []
        assert catalog.geo_hierarchies == []
        assert catalog.metrics == []
        assert catalog.materializations == []
        assert catalog.comparability_rules is None

    def test_create_with_all_assets(self) -> None:
        dataset = make_dataset("sales")
        dimension = make_dimension("product")
        geo_hierarchy = make_geo_hierarchy("sa_hierarchy")
        metric = make_simple_metric("total_sales", "sales")
        materialization = make_materialization("sales_mat", "sales", ["total_sales"])
        rules = make_comparability_rules()

        catalog = SemanticCatalog.create(
            datasets=[dataset],
            dimensions=[dimension],
            geo_hierarchies=[geo_hierarchy],
            metrics=[metric],
            materializations=[materialization],
            comparability_rules=rules,
        )

        assert len(catalog.datasets) == 1
        assert len(catalog.dimensions) == 1
        assert len(catalog.geo_hierarchies) == 1
        assert len(catalog.metrics) == 1
        assert len(catalog.materializations) == 1
        assert catalog.comparability_rules is not None

    def test_direct_construction(self) -> None:
        catalog = SemanticCatalog(
            datasets=[],
            dimensions=[],
            geo_hierarchies=[],
            metrics=[],
            materializations=[],
            comparability_rules=None,
        )
        assert catalog is not None


class TestSemanticCatalogDatasetLookup:
    """Tests for dataset lookup methods."""

    def test_get_dataset_found(self) -> None:
        dataset = make_dataset("orders")
        catalog = SemanticCatalog.create(datasets=[dataset])

        result = catalog.get_dataset("orders")
        assert result is not None
        assert result.name == "orders"

    def test_get_dataset_not_found(self) -> None:
        catalog = SemanticCatalog.create()
        result = catalog.get_dataset("nonexistent")
        assert result is None

    def test_get_dataset_multiple(self) -> None:
        datasets = [make_dataset("orders"), make_dataset("products")]
        catalog = SemanticCatalog.create(datasets=datasets)

        assert catalog.get_dataset("orders") is not None
        assert catalog.get_dataset("products") is not None
        assert catalog.get_dataset("missing") is None


class TestSemanticCatalogDimensionLookup:
    """Tests for dimension lookup methods."""

    def test_get_dimension_found(self) -> None:
        dimension = make_dimension("category")
        catalog = SemanticCatalog.create(dimensions=[dimension])

        result = catalog.get_dimension("category")
        assert result is not None
        assert result.name == "category"

    def test_get_dimension_not_found(self) -> None:
        catalog = SemanticCatalog.create()
        result = catalog.get_dimension("nonexistent")
        assert result is None


class TestSemanticCatalogGeoHierarchyLookup:
    """Tests for geo hierarchy lookup methods."""

    def test_get_geo_hierarchy_found(self) -> None:
        hierarchy = make_geo_hierarchy("admin_boundaries")
        catalog = SemanticCatalog.create(geo_hierarchies=[hierarchy])

        result = catalog.get_geo_hierarchy("admin_boundaries")
        assert result is not None
        assert result.name == "admin_boundaries"

    def test_get_geo_hierarchy_not_found(self) -> None:
        catalog = SemanticCatalog.create()
        result = catalog.get_geo_hierarchy("nonexistent")
        assert result is None


class TestSemanticCatalogMetricLookup:
    """Tests for metric lookup methods."""

    def test_get_metric_found(self) -> None:
        metric = make_simple_metric("revenue", "sales")
        catalog = SemanticCatalog.create(metrics=[metric])

        result = catalog.get_metric("revenue")
        assert result is not None
        assert result.name == "revenue"

    def test_get_metric_not_found(self) -> None:
        catalog = SemanticCatalog.create()
        result = catalog.get_metric("nonexistent")
        assert result is None


class TestSemanticCatalogMaterializationLookup:
    """Tests for materialization lookup methods."""

    def test_get_materialization_found(self) -> None:
        mat = make_materialization("sales_rollup", "sales", ["total"])
        catalog = SemanticCatalog.create(materializations=[mat])

        result = catalog.get_materialization("sales_rollup")
        assert result is not None
        assert result.name == "sales_rollup"

    def test_get_materialization_not_found(self) -> None:
        catalog = SemanticCatalog.create()
        result = catalog.get_materialization("nonexistent")
        assert result is None


class TestSemanticCatalogMetricsForDataset:
    """Tests for get_metrics_for_dataset method."""

    def test_get_metrics_for_dataset_found(self) -> None:
        metric1 = make_simple_metric("total_sales", "sales")
        metric2 = make_simple_metric("avg_sales", "sales")
        metric3 = make_simple_metric("total_orders", "orders")
        catalog = SemanticCatalog.create(metrics=[metric1, metric2, metric3])

        result = catalog.get_metrics_for_dataset("sales")
        assert len(result) == 2
        names = {m.name for m in result}
        assert names == {"total_sales", "avg_sales"}

    def test_get_metrics_for_dataset_not_found(self) -> None:
        metric = make_simple_metric("total", "sales")
        catalog = SemanticCatalog.create(metrics=[metric])

        result = catalog.get_metrics_for_dataset("nonexistent")
        assert result == []

    def test_get_metrics_for_dataset_derived_not_included(self) -> None:
        simple = make_simple_metric("base", "sales")
        derived = make_derived_metric("calc", ["base"])
        catalog = SemanticCatalog.create(metrics=[simple, derived])

        # Derived metrics don't have dataset_name directly
        result = catalog.get_metrics_for_dataset("sales")
        assert len(result) == 1
        assert result[0].name == "base"


class TestSemanticCatalogDependencyResolution:
    """Tests for resolve_metric_dependencies method."""

    def test_resolve_simple_metric_no_deps(self) -> None:
        metric = make_simple_metric("total", "sales")
        catalog = SemanticCatalog.create(metrics=[metric])

        result = catalog.resolve_metric_dependencies(["total"])
        assert len(result) == 1
        assert result[0].name == "total"

    def test_resolve_derived_metric_includes_deps(self) -> None:
        base1 = make_simple_metric("count", "sales")
        base2 = make_simple_metric("sum", "sales")
        derived = make_derived_metric("average", ["count", "sum"])
        catalog = SemanticCatalog.create(metrics=[base1, base2, derived])

        result = catalog.resolve_metric_dependencies(["average"])
        assert len(result) == 3
        names = [m.name for m in result]
        # Dependencies should come before dependents (topological order)
        assert names.index("count") < names.index("average")
        assert names.index("sum") < names.index("average")

    def test_resolve_ratio_metric_includes_deps(self) -> None:
        numerator = make_simple_metric("successes", "events")
        denominator = make_simple_metric("total_events", "events")
        ratio = make_ratio_metric("success_rate", "successes", "total_events")
        catalog = SemanticCatalog.create(metrics=[numerator, denominator, ratio])

        result = catalog.resolve_metric_dependencies(["success_rate"])
        assert len(result) == 3
        names = [m.name for m in result]
        # Numerator and denominator should come before ratio
        assert names.index("successes") < names.index("success_rate")
        assert names.index("total_events") < names.index("success_rate")

    def test_resolve_transitive_dependencies(self) -> None:
        base = make_simple_metric("base", "data")
        middle = make_derived_metric("middle", ["base"])
        top = make_derived_metric("top", ["middle"])
        catalog = SemanticCatalog.create(metrics=[base, middle, top])

        result = catalog.resolve_metric_dependencies(["top"])
        assert len(result) == 3
        names = [m.name for m in result]
        # Topological order: base -> middle -> top
        assert names.index("base") < names.index("middle")
        assert names.index("middle") < names.index("top")

    def test_resolve_multiple_metrics_deduplicates(self) -> None:
        base = make_simple_metric("base", "data")
        derived1 = make_derived_metric("d1", ["base"])
        derived2 = make_derived_metric("d2", ["base"])
        catalog = SemanticCatalog.create(metrics=[base, derived1, derived2])

        result = catalog.resolve_metric_dependencies(["d1", "d2"])
        assert len(result) == 3  # base + d1 + d2, base only once
        names = [m.name for m in result]
        assert "base" in names
        assert "d1" in names
        assert "d2" in names

    def test_resolve_unknown_metric_ignored(self) -> None:
        metric = make_simple_metric("known", "data")
        catalog = SemanticCatalog.create(metrics=[metric])

        result = catalog.resolve_metric_dependencies(["known", "unknown"])
        assert len(result) == 1
        assert result[0].name == "known"

    def test_resolve_all_unknown_returns_empty(self) -> None:
        catalog = SemanticCatalog.create()
        result = catalog.resolve_metric_dependencies(["a", "b", "c"])
        assert result == []

    def test_resolve_empty_list_returns_empty(self) -> None:
        metric = make_simple_metric("metric", "data")
        catalog = SemanticCatalog.create(metrics=[metric])

        result = catalog.resolve_metric_dependencies([])
        assert result == []


class TestSemanticCatalogIndexes:
    """Tests for internal index behavior."""

    def test_indexes_built_on_construction(self) -> None:
        dataset = make_dataset("test")
        catalog = SemanticCatalog.create(datasets=[dataset])

        # Index should be immediately available
        assert catalog._datasets_by_name["test"] == dataset

    def test_metric_graph_built_lazily(self) -> None:
        metric = make_simple_metric("test", "data")
        catalog = SemanticCatalog.create(metrics=[metric])

        # Graph should not be built until needed
        assert catalog._metric_graph is None

        # Trigger graph build via dependency resolution
        catalog.resolve_metric_dependencies(["test"])

        # Now graph should exist
        assert catalog._metric_graph is not None

    def test_metrics_by_dataset_index(self) -> None:
        m1 = make_simple_metric("m1", "ds1")
        m2 = make_simple_metric("m2", "ds1")
        m3 = make_simple_metric("m3", "ds2")
        catalog = SemanticCatalog.create(metrics=[m1, m2, m3])

        assert len(catalog._metrics_by_dataset["ds1"]) == 2
        assert len(catalog._metrics_by_dataset["ds2"]) == 1
