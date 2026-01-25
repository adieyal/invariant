"""Integration tests that validate YAML example fixtures.

These tests ensure that:
1. Valid examples pass validation
2. Invalid examples are rejected with the expected error codes
3. Documentation examples stay in sync with actual behavior

Run with: pytest tests/integration/test_examples.py -v
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.use_cases.validate_query import ValidateQueryUseCase
from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.variable import Variable
from invariant.identity.domain.entities.semantic import IndicatorDefinition
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    AggregationType,
    DataProductKind,
    DataType,
    IndicatorType,
    VariableRole,
)
from invariant.shared.contracts.ids import DataProductId, DatasetId, VariableId
from invariant.shared.contracts.value_objects import GrainSpec
from tests.unit.application.fakes import FakeCatalogStore, FakeIdGenerator

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
VALID_EXAMPLES = list((EXAMPLES_DIR / "valid").glob("*.yaml"))
INVALID_EXAMPLES = list((EXAMPLES_DIR / "invalid").glob("*.yaml"))


def load_example(path: Path) -> dict[str, Any]:
    """Load a YAML example file."""
    return yaml.safe_load(path.read_text())


def build_catalog_from_example(
    example: dict[str, Any],
    catalog_store: FakeCatalogStore,
) -> dict[str, DataProductId]:
    """Build catalog entities from example definition.

    Returns a mapping of example data_product_id strings to actual DataProductIds.
    """
    dp_id_map: dict[str, DataProductId] = {}
    var_id_map: dict[str, VariableId] = {}

    catalog = example.get("catalog", {})

    # Build data products
    for dp_def in catalog.get("data_products", []):
        dp_id = DataProductId.create()
        dp_id_map[dp_def["id"]] = dp_id

        variables: list[Variable] = []
        grain_key_ids: list[VariableId] = []

        for var_def in dp_def.get("variables", []):
            var_id = VariableId.create()
            var_key = f"{dp_def['id']}:{var_def['name']}"
            var_id_map[var_key] = var_id

            var = Variable(
                id=var_id,
                data_product_id=dp_id,
                name=var_def["name"],
                role=VariableRole[var_def["role"]],
                data_type=DataType[var_def["data_type"]],
            )
            variables.append(var)

            if var_def["name"] in dp_def.get("grain_keys", []):
                grain_key_ids.append(var_id)

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name=dp_def["name"],
            kind=DataProductKind[dp_def["kind"]],
            grain=GrainSpec(keys=grain_key_ids),
            variables=variables,
        )
        catalog_store.save_data_product(dp)

    # Build indicator definitions
    for ind_def in catalog.get("indicator_definitions", []):
        # Find the variable ID
        dp_id_str = ind_def["data_product_id"]
        var_name = ind_def["variable_id"]
        var_key = f"{dp_id_str}:{var_name}"
        var_id = var_id_map.get(var_key)

        if var_id is None:
            raise ValueError(f"Variable {var_key} not found for indicator definition")

        policy = AggregationPolicy[ind_def["aggregation_policy"]]

        allowed_aggs: tuple[AggregationType, ...] = ()
        if "allowed_aggregations" in ind_def:
            allowed_aggs = tuple(
                AggregationType[a] for a in ind_def["allowed_aggregations"]
            )

        indicator = IndicatorDefinition(
            variable_id=var_id,
            indicator_type=IndicatorType[ind_def["indicator_type"]],
            aggregation_policy=policy,
            numerator_ref=ind_def.get("numerator_ref"),
            denominator_ref=ind_def.get("denominator_ref"),
            allowed_aggregations=allowed_aggs if allowed_aggs else None,
        )
        catalog_store.save_indicator_definition(indicator)

    return dp_id_map


def build_query_request(
    example: dict[str, Any],
    dp_id_map: dict[str, DataProductId],
) -> QueryRequest:
    """Build a QueryRequest from example definition."""
    query = example["query"]

    selections = []
    for sel in query["selections"]:
        # Map example dp_id to actual UUID
        actual_dp_id = dp_id_map[sel["data_product_id"]]

        metrics = [
            MetricRequest(
                variable=m["variable"],
                aggregation=m["aggregation"],
            )
            for m in sel["metrics"]
        ]

        selections.append(
            DataProductSelectionRequest(
                data_product_id=str(actual_dp_id.value),
                dimensions=sel["dimensions"],
                metrics=metrics,
            )
        )

    return QueryRequest(
        intent=query["intent"],
        selections=selections,
    )


class TestValidExamples:
    """Test that all valid examples pass validation."""

    @pytest.fixture
    def catalog_store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def id_generator(self) -> FakeIdGenerator:
        return FakeIdGenerator()

    @pytest.mark.parametrize(
        "example_path",
        VALID_EXAMPLES,
        ids=[p.stem for p in VALID_EXAMPLES],
    )
    def test_valid_example_passes(
        self,
        example_path: Path,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
    ) -> None:
        """Valid examples should pass validation with ALLOW status."""
        example = load_example(example_path)

        # Build catalog from example definition
        dp_id_map = build_catalog_from_example(example, catalog_store)

        # Build query request
        request = build_query_request(example, dp_id_map)

        # Run validation
        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )
        result = use_case.execute(request)

        # Assert expected outcome
        expected = example["expected"]
        assert result.status == expected["status"], (
            f"Example '{example['id']}' expected status {expected['status']}, "
            f"got {result.status}. Issues: {[i.code for i in result.issues]}"
        )

        if expected.get("issues"):
            expected_codes = {i["code"] for i in expected["issues"]}
            actual_codes = {i.code for i in result.issues}
            assert expected_codes == actual_codes


class TestInvalidExamples:
    """Test that all invalid examples are rejected with expected errors."""

    @pytest.fixture
    def catalog_store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def id_generator(self) -> FakeIdGenerator:
        return FakeIdGenerator()

    @pytest.mark.parametrize(
        "example_path",
        INVALID_EXAMPLES,
        ids=[p.stem for p in INVALID_EXAMPLES],
    )
    def test_invalid_example_rejected(
        self,
        example_path: Path,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
    ) -> None:
        """Invalid examples should be rejected with the specified error code."""
        example = load_example(example_path)

        # Build catalog from example definition
        dp_id_map = build_catalog_from_example(example, catalog_store)

        # Build query request
        request = build_query_request(example, dp_id_map)

        # Run validation
        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )
        result = use_case.execute(request)

        # Assert expected outcome
        expected = example["expected"]
        assert result.status == expected["status"], (
            f"Example '{example['id']}' expected status {expected['status']}, "
            f"got {result.status}"
        )

        # Check that the expected violation is present
        violates = example.get("violates", {})
        expected_code = violates.get("code")
        if expected_code:
            actual_codes = [i.code for i in result.issues]
            assert expected_code in actual_codes, (
                f"Example '{example['id']}' expected issue code {expected_code}, "
                f"got {actual_codes}"
            )


class TestExampleStructure:
    """Test that example files have required structure."""

    @pytest.mark.parametrize(
        "example_path",
        VALID_EXAMPLES + INVALID_EXAMPLES,
        ids=[p.stem for p in VALID_EXAMPLES + INVALID_EXAMPLES],
    )
    def test_example_has_required_fields(self, example_path: Path) -> None:
        """All examples must have required documentation fields."""
        example = load_example(example_path)

        assert "id" in example, f"{example_path.name} missing 'id' field"
        assert "description" in example, f"{example_path.name} missing 'description'"
        assert "teaches" in example, f"{example_path.name} missing 'teaches' field"
        assert isinstance(example["teaches"], list), "'teaches' must be a list"
        assert len(example["teaches"]) > 0, "'teaches' must have at least one item"
        assert "catalog" in example, f"{example_path.name} missing 'catalog'"
        assert "query" in example, f"{example_path.name} missing 'query'"
        assert "expected" in example, f"{example_path.name} missing 'expected'"

    @pytest.mark.parametrize(
        "example_path",
        INVALID_EXAMPLES,
        ids=[p.stem for p in INVALID_EXAMPLES],
    )
    def test_invalid_example_has_violates(self, example_path: Path) -> None:
        """Invalid examples must specify what rule they violate."""
        example = load_example(example_path)

        assert "violates" in example, f"{example_path.name} missing 'violates'"
        assert "code" in example["violates"], "'violates' must have 'code'"
