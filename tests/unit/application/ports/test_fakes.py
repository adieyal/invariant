"""Tests for in-memory fakes."""

from datetime import date, datetime

import pytest

from invariant.domain.model.comparability_rules import (
    ComparabilityPolicy,
    ComparabilityRules,
)
from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.dataset import Dataset
from invariant.domain.model.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.domain.model.enums import DataProductKind, VariableRole
from invariant.domain.model.geo_hierarchy import GeoHierarchy
from invariant.domain.model.ids import (
    DataProductId,
    DatasetId,
    ReferenceSystemId,
    StudyId,
    VariableId,
)
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
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
)
from invariant.domain.model.study import Study
from invariant.domain.model.value_objects import GrainSpec
from invariant.domain.model.variable import Variable
from tests.unit.application.fakes import (
    FakeAuditLog,
    FakeCatalogStore,
    FakeClock,
    FakeIdGenerator,
    FakeSemanticAssetStore,
)


class TestFakeClock:
    def test_now_returns_configured_time(self) -> None:
        clock = FakeClock()
        assert clock.now() == datetime(2024, 1, 15, 10, 0, 0)

    def test_today_returns_date_part(self) -> None:
        clock = FakeClock()
        assert clock.today() == date(2024, 1, 15)

    def test_set_now(self) -> None:
        clock = FakeClock()
        clock.set_now(datetime(2025, 6, 1, 12, 30, 0))
        assert clock.now() == datetime(2025, 6, 1, 12, 30, 0)

    def test_advance(self) -> None:
        clock = FakeClock()
        clock.advance(days=5, hours=2)
        assert clock.now() == datetime(2024, 1, 20, 12, 0, 0)


class TestFakeIdGenerator:
    def test_generates_unique_ids(self) -> None:
        gen = FakeIdGenerator()
        id1 = gen.generate_study_id()
        id2 = gen.generate_study_id()
        assert id1 != id2

    def test_generates_query_ids(self) -> None:
        gen = FakeIdGenerator(_prefix="test")
        qid1 = gen.generate_query_id()
        qid2 = gen.generate_query_id()
        assert qid1 == "test-query-1"
        assert qid2 == "test-query-2"

    def test_different_id_types(self) -> None:
        gen = FakeIdGenerator()
        study_id = gen.generate_study_id()
        dataset_id = gen.generate_dataset_id()
        dp_id = gen.generate_data_product_id()
        # All should be different UUIDs
        assert str(study_id.value) != str(dataset_id.value)
        assert str(dataset_id.value) != str(dp_id.value)


class TestFakeCatalogStore:
    @pytest.fixture
    def store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def sample_study(self) -> Study:
        return Study(
            id=StudyId.create(),
            name="Census 2021",
            owner_org="Stats SA",
        )

    @pytest.fixture
    def sample_dataset(self, sample_study: Study) -> Dataset:
        return Dataset(
            id=DatasetId.create(),
            study_id=sample_study.id,
            name="Demographics",
            reference_system_id=ReferenceSystemId.create(),
        )

    def test_save_and_get_study(
        self, store: FakeCatalogStore, sample_study: Study
    ) -> None:
        store.save_study(sample_study)
        retrieved = store.get_study(sample_study.id)
        assert retrieved is not None
        assert retrieved.name == "Census 2021"

    def test_get_nonexistent_study_returns_none(self, store: FakeCatalogStore) -> None:
        result = store.get_study(StudyId.create())
        assert result is None

    def test_list_studies(self, store: FakeCatalogStore, sample_study: Study) -> None:
        store.save_study(sample_study)
        studies = store.list_studies()
        assert len(studies) == 1
        assert studies[0].id == sample_study.id

    def test_save_and_get_dataset(
        self, store: FakeCatalogStore, sample_dataset: Dataset
    ) -> None:
        store.save_dataset(sample_dataset)
        retrieved = store.get_dataset(sample_dataset.id)
        assert retrieved is not None
        assert retrieved.name == "Demographics"

    def test_list_datasets_filters_by_study(self, store: FakeCatalogStore) -> None:
        study1 = Study(id=StudyId.create(), name="Study 1", owner_org="Pub")
        study2 = Study(id=StudyId.create(), name="Study 2", owner_org="Pub")
        ref_sys = ReferenceSystemId.create()

        ds1 = Dataset(
            id=DatasetId.create(),
            study_id=study1.id,
            name="DS1",
            reference_system_id=ref_sys,
        )
        ds2 = Dataset(
            id=DatasetId.create(),
            study_id=study2.id,
            name="DS2",
            reference_system_id=ref_sys,
        )

        store.save_dataset(ds1)
        store.save_dataset(ds2)

        all_datasets = store.list_datasets()
        assert len(all_datasets) == 2

        study1_datasets = store.list_datasets(study_id=study1.id)
        assert len(study1_datasets) == 1
        assert study1_datasets[0].name == "DS1"

    def test_save_and_get_data_product(self, store: FakeCatalogStore) -> None:
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geo",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name="Pop by Geo",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[var.id]),
            variables=[var],
        )
        store.save_data_product(dp)
        retrieved = store.get_data_product(dp_id)
        assert retrieved is not None
        assert retrieved.name == "Pop by Geo"

    def test_get_catalog_snapshot(self, store: FakeCatalogStore) -> None:
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geo",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name="Test DP",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[var.id]),
            variables=[var],
        )
        store.save_data_product(dp)

        snapshot = store.get_catalog_snapshot({dp_id})
        assert dp_id in snapshot.data_products
        assert snapshot.data_products[dp_id].name == "Test DP"


class TestFakeAuditLog:
    def test_record_and_check_acknowledgment(self) -> None:
        audit = FakeAuditLog()
        query_id = "q-123"

        assert audit.is_acknowledged(query_id) is False

        audit.record_acknowledgment(query_id, ["ISSUE_1"], user_id="user-1")

        assert audit.is_acknowledged(query_id) is True


class TestFakeSemanticAssetStore:
    @pytest.fixture
    def store(self) -> FakeSemanticAssetStore:
        return FakeSemanticAssetStore()

    @pytest.fixture
    def sample_dataset(self) -> SemanticDataset:
        return SemanticDataset.create(
            name="demographics",
            physical_ref=PhysicalRef("public", "demographics"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_level", "geo_code"]),
        )

    @pytest.fixture
    def sample_dimension(self) -> Dimension:
        return Dimension.create(
            name="gender",
            attributes={
                "code": DimensionAttribute(
                    "code", DataType.STRING, SemanticType.CATEGORY
                ),
                "label": DimensionAttribute(
                    "label", DataType.STRING, SemanticType.CATEGORY
                ),
            },
        )

    @pytest.fixture
    def sample_geo_hierarchy(self) -> GeoHierarchy:
        return GeoHierarchy.create(
            name="sa_admin",
            levels=["country", "province", "municipality", "ward"],
        )

    @pytest.fixture
    def sample_metric(self) -> Metric:
        return Metric.create_simple_agg(
            name="total_population",
            dataset_name="demographics",
            expr="population",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )

    @pytest.fixture
    def sample_materialization(self) -> Materialization:
        return Materialization.create(
            name="pop_by_province",
            source=MaterializationSource(SourceType.PROFILE),
            dataset_name="demographics",
            grain=MaterializationGrain(geo_level="province"),
            metrics=["total_population"],
            refresh=RefreshConfig(RefreshStrategy.MANUAL),
            storage=StorageConfig("cache", "pop_by_province"),
        )

    def test_add_and_get_dataset(
        self, store: FakeSemanticAssetStore, sample_dataset: SemanticDataset
    ) -> None:
        store.add_dataset(sample_dataset)
        retrieved = store.get_dataset("demographics")
        assert retrieved is not None
        assert retrieved.name == "demographics"
        assert retrieved.id == sample_dataset.id

    def test_get_nonexistent_dataset_returns_none(
        self, store: FakeSemanticAssetStore
    ) -> None:
        result = store.get_dataset("nonexistent")
        assert result is None

    def test_add_and_get_dimension(
        self, store: FakeSemanticAssetStore, sample_dimension: Dimension
    ) -> None:
        store.add_dimension(sample_dimension)
        retrieved = store.get_dimension("gender")
        assert retrieved is not None
        assert retrieved.name == "gender"
        assert retrieved.id == sample_dimension.id

    def test_get_nonexistent_dimension_returns_none(
        self, store: FakeSemanticAssetStore
    ) -> None:
        result = store.get_dimension("nonexistent")
        assert result is None

    def test_add_and_get_geo_hierarchy(
        self, store: FakeSemanticAssetStore, sample_geo_hierarchy: GeoHierarchy
    ) -> None:
        store.add_geo_hierarchy(sample_geo_hierarchy)
        retrieved = store.get_geo_hierarchy("sa_admin")
        assert retrieved is not None
        assert retrieved.name == "sa_admin"
        assert retrieved.id == sample_geo_hierarchy.id

    def test_get_nonexistent_geo_hierarchy_returns_none(
        self, store: FakeSemanticAssetStore
    ) -> None:
        result = store.get_geo_hierarchy("nonexistent")
        assert result is None

    def test_add_and_get_metric(
        self, store: FakeSemanticAssetStore, sample_metric: Metric
    ) -> None:
        store.add_metric(sample_metric)
        retrieved = store.get_metric("total_population")
        assert retrieved is not None
        assert retrieved.name == "total_population"
        assert retrieved.id == sample_metric.id

    def test_get_nonexistent_metric_returns_none(
        self, store: FakeSemanticAssetStore
    ) -> None:
        result = store.get_metric("nonexistent")
        assert result is None

    def test_add_and_get_materialization(
        self, store: FakeSemanticAssetStore, sample_materialization: Materialization
    ) -> None:
        store.add_materialization(sample_materialization)
        retrieved = store.get_materialization("pop_by_province")
        assert retrieved is not None
        assert retrieved.name == "pop_by_province"
        assert retrieved.id == sample_materialization.id

    def test_get_nonexistent_materialization_returns_none(
        self, store: FakeSemanticAssetStore
    ) -> None:
        result = store.get_materialization("nonexistent")
        assert result is None

    def test_set_and_get_comparability_rules(
        self, store: FakeSemanticAssetStore
    ) -> None:
        rules = ComparabilityRules.create(
            default_policy=ComparabilityPolicy.FORBID,
            forbid_on_mismatch=["methodology_id"],
        )
        store.set_comparability_rules(rules)
        retrieved = store.get_comparability_rules()
        assert retrieved.default_policy == ComparabilityPolicy.FORBID
        assert retrieved.id == rules.id

    def test_get_comparability_rules_returns_default_when_not_set(
        self, store: FakeSemanticAssetStore
    ) -> None:
        rules = store.get_comparability_rules()
        # Should return a default rules instance
        assert rules is not None
        assert rules.default_policy == ComparabilityPolicy.WARN

    def test_load_catalog_returns_all_assets(
        self,
        store: FakeSemanticAssetStore,
        sample_dataset: SemanticDataset,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_metric: Metric,
        sample_materialization: Materialization,
    ) -> None:
        store.add_dataset(sample_dataset)
        store.add_dimension(sample_dimension)
        store.add_geo_hierarchy(sample_geo_hierarchy)
        store.add_metric(sample_metric)
        store.add_materialization(sample_materialization)

        catalog = store.load_catalog()

        assert len(catalog.datasets) == 1
        assert len(catalog.dimensions) == 1
        assert len(catalog.geo_hierarchies) == 1
        assert len(catalog.metrics) == 1
        assert len(catalog.materializations) == 1
        assert catalog.get_dataset("demographics") is not None
        assert catalog.get_dimension("gender") is not None
        assert catalog.get_geo_hierarchy("sa_admin") is not None
        assert catalog.get_metric("total_population") is not None
        assert catalog.get_materialization("pop_by_province") is not None

    def test_load_catalog_includes_comparability_rules(
        self, store: FakeSemanticAssetStore
    ) -> None:
        rules = ComparabilityRules.create(default_policy=ComparabilityPolicy.FORBID)
        store.set_comparability_rules(rules)

        catalog = store.load_catalog()

        assert catalog.comparability_rules is not None
        assert catalog.comparability_rules.default_policy == ComparabilityPolicy.FORBID

    def test_load_catalog_without_comparability_rules(
        self, store: FakeSemanticAssetStore
    ) -> None:
        catalog = store.load_catalog()
        # Should be None if not configured
        assert catalog.comparability_rules is None

    def test_clear_removes_all_assets(
        self,
        store: FakeSemanticAssetStore,
        sample_dataset: SemanticDataset,
        sample_dimension: Dimension,
        sample_metric: Metric,
    ) -> None:
        store.add_dataset(sample_dataset)
        store.add_dimension(sample_dimension)
        store.add_metric(sample_metric)

        store.clear()

        assert store.get_dataset("demographics") is None
        assert store.get_dimension("gender") is None
        assert store.get_metric("total_population") is None
        catalog = store.load_catalog()
        assert len(catalog.datasets) == 0
        assert len(catalog.dimensions) == 0
        assert len(catalog.metrics) == 0

    def test_overwrite_asset_with_same_name(
        self, store: FakeSemanticAssetStore
    ) -> None:
        dataset1 = SemanticDataset.create(
            name="demographics",
            physical_ref=PhysicalRef("public", "demographics_v1"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_level"]),
        )
        dataset2 = SemanticDataset.create(
            name="demographics",
            physical_ref=PhysicalRef("public", "demographics_v2"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_level"]),
        )

        store.add_dataset(dataset1)
        store.add_dataset(dataset2)

        retrieved = store.get_dataset("demographics")
        assert retrieved is not None
        # Should be the second one (overwritten)
        assert retrieved.id == dataset2.id
        assert retrieved.physical_ref.table == "demographics_v2"

    def test_protocol_compliance(self, store: FakeSemanticAssetStore) -> None:
        """Verify FakeSemanticAssetStore implements SemanticAssetStore protocol."""
        from invariant.application.ports.semantic_asset_store import SemanticAssetStore

        # Protocol compliance is verified by duck typing
        # If this doesn't raise, the fake implements the protocol
        def use_store(s: SemanticAssetStore) -> None:
            s.load_catalog()
            s.get_dataset("test")
            s.get_dimension("test")
            s.get_geo_hierarchy("test")
            s.get_metric("test")
            s.get_materialization("test")
            s.get_comparability_rules()

        use_store(store)  # Should not raise
