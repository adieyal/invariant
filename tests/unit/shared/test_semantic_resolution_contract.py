"""Tests for SemanticResolution boundary contract."""

from __future__ import annotations

import pytest

from invariant.shared.contracts.semantic_resolution import (
    AmbiguousRef,
    MissingRef,
    RefType,
    ResolutionStatus,
    ResolvedDimension,
    ResolvedMetric,
    SemanticResolution,
)


class TestResolutionStatusEnum:
    """Tests for ResolutionStatus enum."""

    def test_resolution_status_enum(self) -> None:
        """ResolutionStatus has RESOLVED, INCOMPLETE, ERROR values."""
        assert ResolutionStatus.RESOLVED.value == "RESOLVED"
        assert ResolutionStatus.INCOMPLETE.value == "INCOMPLETE"
        assert ResolutionStatus.ERROR.value == "ERROR"

    def test_resolution_status_is_string_enum(self) -> None:
        """ResolutionStatus values are strings."""
        assert isinstance(ResolutionStatus.RESOLVED.value, str)
        assert isinstance(ResolutionStatus.INCOMPLETE.value, str)
        assert isinstance(ResolutionStatus.ERROR.value, str)


class TestRefTypeEnum:
    """Tests for RefType enum."""

    def test_ref_type_enum(self) -> None:
        """RefType has METRIC and DIMENSION values."""
        assert RefType.METRIC.value == "METRIC"
        assert RefType.DIMENSION.value == "DIMENSION"


class TestResolvedMetric:
    """Tests for ResolvedMetric value object."""

    def test_resolved_metric_is_frozen(self) -> None:
        """ResolvedMetric cannot be modified."""
        resolved = ResolvedMetric(
            name="total_population",
            metric_id="metric-123",
            dependencies=("base_count",),
        )
        with pytest.raises(AttributeError):
            resolved.name = "changed"  # type: ignore[misc]

    def test_resolved_metric_creation(self) -> None:
        """ResolvedMetric holds metric resolution data."""
        resolved = ResolvedMetric(
            name="rate",
            metric_id="metric-456",
            dependencies=("numerator", "denominator"),
        )
        assert resolved.name == "rate"
        assert resolved.metric_id == "metric-456"
        assert resolved.dependencies == ("numerator", "denominator")

    def test_resolved_metric_empty_dependencies(self) -> None:
        """ResolvedMetric can have empty dependencies."""
        resolved = ResolvedMetric(
            name="simple_count",
            metric_id="metric-789",
            dependencies=(),
        )
        assert resolved.dependencies == ()

    def test_resolved_metric_to_dict(self) -> None:
        """ResolvedMetric can be serialized to dict."""
        resolved = ResolvedMetric(
            name="total",
            metric_id="metric-001",
            dependencies=("base",),
        )
        data = resolved.to_dict()
        assert data["name"] == "total"
        assert data["metric_id"] == "metric-001"
        assert data["dependencies"] == ["base"]

    def test_resolved_metric_from_dict(self) -> None:
        """ResolvedMetric can be deserialized from dict."""
        data = {
            "name": "total",
            "metric_id": "metric-001",
            "dependencies": ["base"],
        }
        resolved = ResolvedMetric.from_dict(data)
        assert resolved.name == "total"
        assert resolved.metric_id == "metric-001"
        assert resolved.dependencies == ("base",)


class TestResolvedDimension:
    """Tests for ResolvedDimension value object."""

    def test_resolved_dimension_is_frozen(self) -> None:
        """ResolvedDimension cannot be modified."""
        resolved = ResolvedDimension(
            name="geography",
            dimension_id="dim-123",
            attributes=("code", "name", "level"),
        )
        with pytest.raises(AttributeError):
            resolved.name = "changed"  # type: ignore[misc]

    def test_resolved_dimension_creation(self) -> None:
        """ResolvedDimension holds dimension resolution data."""
        resolved = ResolvedDimension(
            name="time",
            dimension_id="dim-456",
            attributes=("year", "month"),
        )
        assert resolved.name == "time"
        assert resolved.dimension_id == "dim-456"
        assert resolved.attributes == ("year", "month")

    def test_resolved_dimension_to_dict(self) -> None:
        """ResolvedDimension can be serialized to dict."""
        resolved = ResolvedDimension(
            name="category",
            dimension_id="dim-001",
            attributes=("code", "label"),
        )
        data = resolved.to_dict()
        assert data["name"] == "category"
        assert data["dimension_id"] == "dim-001"
        assert data["attributes"] == ["code", "label"]

    def test_resolved_dimension_from_dict(self) -> None:
        """ResolvedDimension can be deserialized from dict."""
        data = {
            "name": "category",
            "dimension_id": "dim-001",
            "attributes": ["code", "label"],
        }
        resolved = ResolvedDimension.from_dict(data)
        assert resolved.name == "category"
        assert resolved.dimension_id == "dim-001"
        assert resolved.attributes == ("code", "label")


class TestMissingRef:
    """Tests for MissingRef value object."""

    def test_missing_ref_captures_what_is_missing(self) -> None:
        """MissingRef includes ref_name and ref_type."""
        missing = MissingRef(
            ref_name="unknown_metric",
            ref_type=RefType.METRIC,
        )
        assert missing.ref_name == "unknown_metric"
        assert missing.ref_type == RefType.METRIC

    def test_missing_ref_is_frozen(self) -> None:
        """MissingRef cannot be modified."""
        missing = MissingRef(
            ref_name="missing_dim",
            ref_type=RefType.DIMENSION,
        )
        with pytest.raises(AttributeError):
            missing.ref_name = "changed"  # type: ignore[misc]

    def test_missing_ref_to_dict(self) -> None:
        """MissingRef can be serialized to dict."""
        missing = MissingRef(
            ref_name="unknown",
            ref_type=RefType.METRIC,
        )
        data = missing.to_dict()
        assert data["ref_name"] == "unknown"
        assert data["ref_type"] == "METRIC"

    def test_missing_ref_from_dict(self) -> None:
        """MissingRef can be deserialized from dict."""
        data = {
            "ref_name": "unknown",
            "ref_type": "DIMENSION",
        }
        missing = MissingRef.from_dict(data)
        assert missing.ref_name == "unknown"
        assert missing.ref_type == RefType.DIMENSION


class TestAmbiguousRef:
    """Tests for AmbiguousRef value object."""

    def test_ambiguous_ref_captures_candidates(self) -> None:
        """AmbiguousRef includes ref_name, ref_type, and candidates."""
        ambiguous = AmbiguousRef(
            ref_name="population",
            ref_type=RefType.METRIC,
            candidates=("total_population", "urban_population", "rural_population"),
        )
        assert ambiguous.ref_name == "population"
        assert ambiguous.ref_type == RefType.METRIC
        assert ambiguous.candidates == (
            "total_population",
            "urban_population",
            "rural_population",
        )

    def test_ambiguous_ref_is_frozen(self) -> None:
        """AmbiguousRef cannot be modified."""
        ambiguous = AmbiguousRef(
            ref_name="geo",
            ref_type=RefType.DIMENSION,
            candidates=("geography", "geo_code"),
        )
        with pytest.raises(AttributeError):
            ambiguous.ref_name = "changed"  # type: ignore[misc]

    def test_ambiguous_ref_to_dict(self) -> None:
        """AmbiguousRef can be serialized to dict."""
        ambiguous = AmbiguousRef(
            ref_name="pop",
            ref_type=RefType.METRIC,
            candidates=("population", "pop_total"),
        )
        data = ambiguous.to_dict()
        assert data["ref_name"] == "pop"
        assert data["ref_type"] == "METRIC"
        assert data["candidates"] == ["population", "pop_total"]

    def test_ambiguous_ref_from_dict(self) -> None:
        """AmbiguousRef can be deserialized from dict."""
        data = {
            "ref_name": "pop",
            "ref_type": "METRIC",
            "candidates": ["population", "pop_total"],
        }
        ambiguous = AmbiguousRef.from_dict(data)
        assert ambiguous.ref_name == "pop"
        assert ambiguous.ref_type == RefType.METRIC
        assert ambiguous.candidates == ("population", "pop_total")


class TestSemanticResolution:
    """Tests for SemanticResolution boundary contract."""

    def test_semantic_resolution_is_frozen(self) -> None:
        """SemanticResolution cannot be modified after creation."""
        resolution = SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            metrics=(),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=(),
        )
        with pytest.raises(AttributeError):
            resolution.status = ResolutionStatus.ERROR  # type: ignore[misc]

    def test_is_complete_property(self) -> None:
        """is_complete returns True only when status is RESOLVED."""
        resolved = SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            metrics=(ResolvedMetric(name="total", metric_id="m1", dependencies=()),),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=("m1",),
        )
        assert resolved.is_complete is True

        incomplete = SemanticResolution(
            status=ResolutionStatus.INCOMPLETE,
            metrics=(),
            dimensions=(),
            missing_refs=(MissingRef(ref_name="unknown", ref_type=RefType.METRIC),),
            ambiguous_refs=(),
            evaluation_order=(),
        )
        assert incomplete.is_complete is False

        error = SemanticResolution(
            status=ResolutionStatus.ERROR,
            metrics=(),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=(),
        )
        assert error.is_complete is False

    def test_can_proceed_partial_property(self) -> None:
        """can_proceed_partial returns True for RESOLVED and INCOMPLETE."""
        resolved = SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            metrics=(),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=(),
        )
        assert resolved.can_proceed_partial is True

        incomplete = SemanticResolution(
            status=ResolutionStatus.INCOMPLETE,
            metrics=(),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=(),
        )
        assert incomplete.can_proceed_partial is True

        error = SemanticResolution(
            status=ResolutionStatus.ERROR,
            metrics=(),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=(),
        )
        assert error.can_proceed_partial is False

    def test_evaluation_order_is_tuple(self) -> None:
        """evaluation_order is immutable tuple."""
        resolution = SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            metrics=(
                ResolvedMetric(name="base", metric_id="m1", dependencies=()),
                ResolvedMetric(name="derived", metric_id="m2", dependencies=("base",)),
            ),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=("m1", "m2"),
        )
        assert isinstance(resolution.evaluation_order, tuple)
        assert resolution.evaluation_order == ("m1", "m2")

    def test_semantic_resolution_round_trip(self) -> None:
        """to_dict() and from_dict() produce equivalent objects."""
        original = SemanticResolution(
            status=ResolutionStatus.INCOMPLETE,
            metrics=(
                ResolvedMetric(name="count", metric_id="m1", dependencies=()),
                ResolvedMetric(name="rate", metric_id="m2", dependencies=("count",)),
            ),
            dimensions=(
                ResolvedDimension(
                    name="geo", dimension_id="d1", attributes=("code", "name")
                ),
            ),
            missing_refs=(
                MissingRef(ref_name="unknown_metric", ref_type=RefType.METRIC),
            ),
            ambiguous_refs=(
                AmbiguousRef(
                    ref_name="pop",
                    ref_type=RefType.METRIC,
                    candidates=("population", "pop_total"),
                ),
            ),
            evaluation_order=("m1", "m2"),
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = SemanticResolution.from_dict(data)

        # Verify equivalence
        assert restored.status == original.status
        assert len(restored.metrics) == len(original.metrics)
        assert restored.metrics[0].name == original.metrics[0].name
        assert restored.metrics[1].dependencies == original.metrics[1].dependencies
        assert len(restored.dimensions) == len(original.dimensions)
        assert restored.dimensions[0].attributes == original.dimensions[0].attributes
        assert len(restored.missing_refs) == len(original.missing_refs)
        assert restored.missing_refs[0].ref_name == original.missing_refs[0].ref_name
        assert len(restored.ambiguous_refs) == len(original.ambiguous_refs)
        assert (
            restored.ambiguous_refs[0].candidates
            == original.ambiguous_refs[0].candidates
        )
        assert restored.evaluation_order == original.evaluation_order
        assert restored.is_complete == original.is_complete
        assert restored.can_proceed_partial == original.can_proceed_partial

    def test_semantic_resolution_empty_collections(self) -> None:
        """SemanticResolution handles empty collections correctly."""
        resolution = SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            metrics=(),
            dimensions=(),
            missing_refs=(),
            ambiguous_refs=(),
            evaluation_order=(),
        )
        data = resolution.to_dict()
        restored = SemanticResolution.from_dict(data)

        assert restored.metrics == ()
        assert restored.dimensions == ()
        assert restored.missing_refs == ()
        assert restored.ambiguous_refs == ()
        assert restored.evaluation_order == ()

    def test_semantic_resolution_uses_sequence_for_construction(self) -> None:
        """SemanticResolution normalizes sequences to tuples."""
        resolution = SemanticResolution(
            status=ResolutionStatus.RESOLVED,
            metrics=[  # type: ignore[arg-type]
                ResolvedMetric(name="m1", metric_id="id1", dependencies=[]),  # type: ignore[arg-type]
            ],
            dimensions=[],  # type: ignore[arg-type]
            missing_refs=[],  # type: ignore[arg-type]
            ambiguous_refs=[],  # type: ignore[arg-type]
            evaluation_order=["id1"],  # type: ignore[arg-type]
        )
        # All should be converted to tuples
        assert isinstance(resolution.metrics, tuple)
        assert isinstance(resolution.dimensions, tuple)
        assert isinstance(resolution.missing_refs, tuple)
        assert isinstance(resolution.ambiguous_refs, tuple)
        assert isinstance(resolution.evaluation_order, tuple)
