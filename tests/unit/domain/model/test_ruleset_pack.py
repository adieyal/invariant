"""Tests for RulesetPack value objects."""

import pytest

from invariant.domain.model.ruleset_pack import RulesetPack
from invariant.domain.model.validation import Severity


class TestRulesetPack:
    def test_create_minimal_pack(self) -> None:
        pack = RulesetPack(
            id="core",
            version="1.0.0",
            enabled_checks=("INDICATOR_AGGREGATION", "GRAIN_VALIDATION"),
        )

        assert pack.id == "core"
        assert pack.version == "1.0.0"
        assert len(pack.enabled_checks) == 2

    def test_create_full_pack(self) -> None:
        pack = RulesetPack(
            id="regulated",
            version="2.1.0",
            enabled_checks=(
                "INDICATOR_AGGREGATION",
                "COMPARABILITY",
                "FRESHNESS",
            ),
            severity_overrides={
                "FRESHNESS_VIOLATED": Severity.BLOCK,
                "PARTIAL_COMPARABILITY": Severity.REQUIRE_ACK,
            },
            allow_rewrites=False,
            require_ack_for=("GEO_MISMATCH", "UNIVERSE_CONFLICT"),
        )

        assert pack.id == "regulated"
        assert pack.allow_rewrites is False
        assert len(pack.require_ack_for) == 2

    def test_is_enabled(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=("CHECK_A", "CHECK_B"),
        )

        assert pack.is_enabled("CHECK_A") is True
        assert pack.is_enabled("CHECK_B") is True
        assert pack.is_enabled("CHECK_C") is False

    def test_get_severity_without_override(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=("CHECK_A",),
        )

        result = pack.get_severity("CHECK_A", default=Severity.WARN)
        assert result == Severity.WARN

    def test_get_severity_with_override(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=("CHECK_A",),
            severity_overrides={"CHECK_A": Severity.BLOCK},
        )

        result = pack.get_severity("CHECK_A", default=Severity.WARN)
        assert result == Severity.BLOCK

    def test_requires_ack(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=(),
            require_ack_for=("ISSUE_A", "ISSUE_B"),
        )

        assert pack.requires_ack("ISSUE_A") is True
        assert pack.requires_ack("ISSUE_B") is True
        assert pack.requires_ack("ISSUE_C") is False

    def test_allow_rewrites_default_true(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=(),
        )

        assert pack.allow_rewrites is True

    def test_severity_overrides_default_empty(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=(),
        )

        assert pack.severity_overrides == {}

    def test_require_ack_for_default_empty(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=(),
        )

        assert pack.require_ack_for == ()

    def test_pack_is_immutable(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=("CHECK_A",),
        )

        with pytest.raises(AttributeError):
            pack.id = "changed"  # type: ignore

    def test_severity_overrides_are_immutable(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=(),
            severity_overrides={"CHECK_A": Severity.WARN},
        )

        with pytest.raises(TypeError):
            pack.severity_overrides["CHECK_B"] = Severity.BLOCK  # type: ignore


class TestBuiltInPacks:
    def test_core_pack_exists(self) -> None:
        from invariant.domain.model.ruleset_pack import CORE_PACK

        assert CORE_PACK.id == "core"
        assert CORE_PACK.is_enabled("INDICATOR_AGGREGATION")

    def test_standard_pack_exists(self) -> None:
        from invariant.domain.model.ruleset_pack import STANDARD_PACK

        assert STANDARD_PACK.id == "standard"
        assert STANDARD_PACK.is_enabled("COMPARABILITY")

    def test_regulated_pack_exists(self) -> None:
        from invariant.domain.model.ruleset_pack import REGULATED_PACK

        assert REGULATED_PACK.id == "regulated"
        assert REGULATED_PACK.is_enabled("FRESHNESS")
        assert (
            REGULATED_PACK.get_severity("FRESHNESS_VIOLATED", default=Severity.WARN)
            == Severity.BLOCK
        )
