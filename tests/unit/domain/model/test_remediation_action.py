"""Tests for RemediationAction value objects."""

import pytest

from invariant.validation.domain.value_objects.remediation_action import (
    ActionType,
    RemediationAction,
)


class TestActionType:
    def test_action_type_values(self) -> None:
        assert ActionType.REWRITE_PLAN.value == "REWRITE_PLAN"
        assert ActionType.APPLY_CROSSWALK.value == "APPLY_CROSSWALK"
        assert ActionType.ACK_ONLY.value == "ACK_ONLY"
        assert ActionType.UPDATE_CATALOG.value == "UPDATE_CATALOG"
        assert ActionType.DEFINE_INDICATOR.value == "DEFINE_INDICATOR"


class TestRemediationAction:
    def test_create_action_without_parameters(self) -> None:
        action = RemediationAction(
            action_type=ActionType.ACK_ONLY,
            description="Acknowledge risk and proceed",
        )

        assert action.action_type == ActionType.ACK_ONLY
        assert action.description == "Acknowledge risk and proceed"
        assert action.parameters == {}

    def test_create_action_with_parameters(self) -> None:
        action = RemediationAction(
            action_type=ActionType.APPLY_CROSSWALK,
            description="Apply 2020→2023 boundary crosswalk",
            parameters={
                "crosswalk_id": "cw-123",
                "method": "AREA_WEIGHTED",
            },
        )

        assert action.action_type == ActionType.APPLY_CROSSWALK
        assert action.description == "Apply 2020→2023 boundary crosswalk"
        assert action.parameters["crosswalk_id"] == "cw-123"
        assert action.parameters["method"] == "AREA_WEIGHTED"

    def test_action_is_immutable(self) -> None:
        action = RemediationAction(
            action_type=ActionType.REWRITE_PLAN,
            description="Rewrite to use recomputation",
        )

        with pytest.raises(AttributeError):
            action.description = "Changed"  # type: ignore

    def test_parameters_are_immutable(self) -> None:
        action = RemediationAction(
            action_type=ActionType.APPLY_CROSSWALK,
            description="Apply crosswalk",
            parameters={"key": "value"},
        )

        with pytest.raises(TypeError):
            action.parameters["new_key"] = "new_value"  # type: ignore

    def test_all_action_types(self) -> None:
        for action_type in ActionType:
            action = RemediationAction(
                action_type=action_type,
                description=f"Action for {action_type.value}",
            )
            assert action.action_type == action_type

    def test_define_indicator_action(self) -> None:
        action = RemediationAction(
            action_type=ActionType.DEFINE_INDICATOR,
            description="Define numerator/denominator for safe recomputation",
            parameters={
                "numerator_ref": "var-123",
                "denominator_ref": "var-456",
            },
        )

        assert action.action_type == ActionType.DEFINE_INDICATOR
        assert "numerator_ref" in action.parameters

    def test_update_catalog_action(self) -> None:
        action = RemediationAction(
            action_type=ActionType.UPDATE_CATALOG,
            description="Add universe definition to dataset",
            parameters={
                "dataset_id": "ds-123",
                "universe_id": "univ-456",
            },
        )

        assert action.action_type == ActionType.UPDATE_CATALOG
        assert action.parameters["dataset_id"] == "ds-123"
