"""Tests for AttributionProvider port."""

import pytest

from invariant.application.ports.attribution_provider import (
    AttributionProvider,
    AttributionRequest,
    NullAttributionProvider,
)
from invariant.domain.model.attribution import (
    Attribution,
    AttributionDimension,
    AttributionSlice,
)
from invariant.domain.model.ids import DatasetId, VariableId


def _make_request() -> AttributionRequest:
    """Create a test attribution request."""
    var_id = VariableId.create()
    return AttributionRequest(
        issue_code="SMALL_CELL_WARNING",
        dataset_id=DatasetId.create(),
        dimensions=(AttributionDimension(variable_id=var_id, name="age_group"),),
        filter_context={"year": 2020},
    )


class TestAttributionRequest:
    def test_create_request(self) -> None:
        var_id = VariableId.create()
        dataset_id = DatasetId.create()

        request = AttributionRequest(
            issue_code="SMALL_CELL_WARNING",
            dataset_id=dataset_id,
            dimensions=(AttributionDimension(variable_id=var_id, name="age_group"),),
            filter_context={"year": 2020},
        )

        assert request.issue_code == "SMALL_CELL_WARNING"
        assert request.dataset_id == dataset_id
        assert len(request.dimensions) == 1
        assert request.filter_context == {"year": 2020}

    def test_request_is_immutable(self) -> None:
        request = _make_request()

        with pytest.raises(AttributeError):
            request.issue_code = "OTHER"  # type: ignore

    def test_request_with_empty_filter_context(self) -> None:
        var_id = VariableId.create()
        request = AttributionRequest(
            issue_code="TEST",
            dataset_id=DatasetId.create(),
            dimensions=(AttributionDimension(variable_id=var_id, name="region"),),
            filter_context={},
        )

        assert request.filter_context == {}

    def test_request_with_multiple_dimensions(self) -> None:
        var_id_1 = VariableId.create()
        var_id_2 = VariableId.create()
        request = AttributionRequest(
            issue_code="TEST",
            dataset_id=DatasetId.create(),
            dimensions=(
                AttributionDimension(variable_id=var_id_1, name="age_group"),
                AttributionDimension(variable_id=var_id_2, name="region"),
            ),
            filter_context={},
        )

        assert len(request.dimensions) == 2


class TestNullAttributionProvider:
    def test_implements_protocol(self) -> None:
        provider = NullAttributionProvider()

        assert isinstance(provider, AttributionProvider)

    def test_returns_unavailable_attribution(self) -> None:
        provider = NullAttributionProvider()
        request = _make_request()

        attribution = provider.compute_attribution(request)

        assert attribution.method == "unavailable"
        assert attribution.slices == ()
        assert attribution.has_slices is False

    def test_always_returns_empty_slices(self) -> None:
        provider = NullAttributionProvider()

        # Multiple requests should all return unavailable
        for _ in range(3):
            request = _make_request()
            attribution = provider.compute_attribution(request)
            assert len(attribution.slices) == 0


class TestAttributionProviderProtocol:
    def test_custom_provider_implementation(self) -> None:
        """Test that a custom provider can implement the protocol."""

        class FakeAttributionProvider:
            def compute_attribution(self, request: AttributionRequest) -> Attribution:
                return Attribution(
                    slices=(
                        AttributionSlice(
                            dimension=request.dimensions[0],
                            value="65+",
                            contribution_score=0.85,
                        ),
                    ),
                    method="exact",
                )

        provider: AttributionProvider = FakeAttributionProvider()
        request = _make_request()

        attribution = provider.compute_attribution(request)

        assert attribution.method == "exact"
        assert len(attribution.slices) == 1
        assert attribution.slices[0].value == "65+"
        assert attribution.slices[0].contribution_score == 0.85
