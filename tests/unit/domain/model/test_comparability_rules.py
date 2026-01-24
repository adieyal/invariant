"""Tests for ComparabilityRules domain entity."""

import pytest

from invariant.domain.model.comparability_rules import (
    ComparabilityPolicy,
    ComparabilityRules,
)
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    Metric,
)
from invariant.domain.model.validation import Severity
from invariant.shared.contracts.ids import ComparabilityRuleId


class TestComparabilityPolicy:
    def test_all_values_exist(self) -> None:
        assert ComparabilityPolicy.ALLOW.value == "ALLOW"
        assert ComparabilityPolicy.WARN.value == "WARN"
        assert ComparabilityPolicy.FORBID.value == "FORBID"

    def test_string_enum(self) -> None:
        assert ComparabilityPolicy.ALLOW == "ALLOW"
        assert ComparabilityPolicy("WARN") == ComparabilityPolicy.WARN


class TestComparabilityRulesConstruction:
    def test_create_with_defaults(self) -> None:
        rules = ComparabilityRules.create()
        assert rules.id is not None
        assert rules.default_policy == ComparabilityPolicy.WARN
        assert rules.forbid_on_mismatch == ()
        assert rules.warn_on_mismatch == ()
        assert rules.allow_override_flag == "allow_incomparable"

    def test_create_with_custom_policy(self) -> None:
        rules = ComparabilityRules.create(default_policy=ComparabilityPolicy.FORBID)
        assert rules.default_policy == ComparabilityPolicy.FORBID

    def test_create_with_forbid_fields(self) -> None:
        rules = ComparabilityRules.create(
            forbid_on_mismatch=["methodology_id", "population_definition"],
        )
        assert rules.forbid_on_mismatch == (
            "methodology_id",
            "population_definition",
        )

    def test_create_with_warn_fields(self) -> None:
        rules = ComparabilityRules.create(
            warn_on_mismatch=["methodology_version"],
        )
        assert rules.warn_on_mismatch == ("methodology_version",)

    def test_create_with_custom_override_flag(self) -> None:
        rules = ComparabilityRules.create(allow_override_flag="skip_comparability")
        assert rules.allow_override_flag == "skip_comparability"

    def test_construct_with_explicit_id(self) -> None:
        rule_id = ComparabilityRuleId.create()
        rules = ComparabilityRules(id=rule_id)
        assert rules.id == rule_id

    def test_frozen(self) -> None:
        rules = ComparabilityRules.create()
        with pytest.raises(AttributeError):
            rules.default_policy = ComparabilityPolicy.ALLOW  # type: ignore[misc]


class TestComparabilityRulesCheckCompatibility:
    @staticmethod
    def _create_metric_with_comparability(
        name: str,
        methodology_id: str = "census_2022",
        methodology_version: str = "1.0",
        population_definition: str | None = "total_population",
    ) -> Metric:
        return Metric.create_simple_agg(
            name=name,
            dataset_name="test_dataset",
            expr="value",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            comparability=Comparability(
                methodology_id=methodology_id,
                methodology_version=methodology_version,
                population_definition=population_definition,
            ),
        )

    @staticmethod
    def _create_metric_without_comparability(name: str) -> Metric:
        return Metric.create_simple_agg(
            name=name,
            dataset_name="test_dataset",
            expr="value",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )

    def test_no_issues_with_single_metric(self) -> None:
        rules = ComparabilityRules.create()
        metric = self._create_metric_with_comparability("metric1")
        issues = rules.check_compatibility([metric])
        assert issues == []

    def test_no_issues_with_empty_metrics(self) -> None:
        rules = ComparabilityRules.create()
        issues = rules.check_compatibility([])
        assert issues == []

    def test_no_issues_when_all_metrics_compatible(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability("metric1")
        m2 = self._create_metric_with_comparability("metric2")
        issues = rules.check_compatibility([m1, m2])
        assert issues == []

    def test_no_issues_when_metrics_lack_comparability(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_without_comparability("metric1")
        m2 = self._create_metric_without_comparability("metric2")
        issues = rules.check_compatibility([m1, m2])
        assert issues == []

    def test_no_issues_when_only_one_has_comparability(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability("metric1")
        m2 = self._create_metric_without_comparability("metric2")
        issues = rules.check_compatibility([m1, m2])
        assert issues == []

    def test_methodology_id_mismatch_default_warn(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_id="census_2022"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_id="survey_2023"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.code == "COMPARABILITY_METHODOLOGY_ID_MISMATCH"
        assert issue.severity == Severity.WARN
        assert "metric1" in issue.message
        assert "metric2" in issue.message
        assert "census_2022" in issue.message
        assert "survey_2023" in issue.message

    def test_methodology_id_mismatch_forbid_policy(self) -> None:
        rules = ComparabilityRules.create(default_policy=ComparabilityPolicy.FORBID)
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_id="census_2022"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_id="survey_2023"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        assert issues[0].severity == Severity.BLOCK

    def test_methodology_id_mismatch_forbid_field_override(self) -> None:
        rules = ComparabilityRules.create(
            default_policy=ComparabilityPolicy.WARN,
            forbid_on_mismatch=["methodology_id"],
        )
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_id="census_2022"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_id="survey_2023"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        assert issues[0].severity == Severity.BLOCK

    def test_methodology_version_mismatch(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_version="1.0"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_version="2.0"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.code == "COMPARABILITY_METHODOLOGY_VERSION_MISMATCH"
        assert "1.0" in issue.message
        assert "2.0" in issue.message

    def test_population_definition_mismatch(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability(
            "metric1", population_definition="total_population"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", population_definition="adults_only"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.code == "COMPARABILITY_POPULATION_DEFINITION_MISMATCH"

    def test_population_definition_none_vs_value(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability(
            "metric1", population_definition=None
        )
        m2 = self._create_metric_with_comparability(
            "metric2", population_definition="adults_only"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        issue = issues[0]
        assert issue.code == "COMPARABILITY_POPULATION_DEFINITION_MISMATCH"
        assert "(none)" in issue.message
        assert "adults_only" in issue.message

    def test_multiple_mismatches(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability(
            "metric1",
            methodology_id="census_2022",
            methodology_version="1.0",
            population_definition="total_population",
        )
        m2 = self._create_metric_with_comparability(
            "metric2",
            methodology_id="survey_2023",
            methodology_version="2.0",
            population_definition="adults_only",
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 3
        codes = {i.code for i in issues}
        assert codes == {
            "COMPARABILITY_METHODOLOGY_ID_MISMATCH",
            "COMPARABILITY_METHODOLOGY_VERSION_MISMATCH",
            "COMPARABILITY_POPULATION_DEFINITION_MISMATCH",
        }

    def test_multiple_metrics_compared_to_reference(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_id="census_2022"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_id="survey_2023"
        )
        m3 = self._create_metric_with_comparability(
            "metric3", methodology_id="admin_2024"
        )
        issues = rules.check_compatibility([m1, m2, m3])

        # m2 vs m1, m3 vs m1
        assert len(issues) == 2

    def test_warn_field_override(self) -> None:
        rules = ComparabilityRules.create(
            default_policy=ComparabilityPolicy.FORBID,
            warn_on_mismatch=["methodology_version"],
        )
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_version="1.0"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_version="2.0"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        assert issues[0].severity == Severity.WARN

    def test_allow_policy_no_issues(self) -> None:
        rules = ComparabilityRules.create(default_policy=ComparabilityPolicy.ALLOW)
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_id="census_2022"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_id="survey_2023"
        )
        issues = rules.check_compatibility([m1, m2])

        # With ALLOW policy, issues still created but with ALLOW severity
        assert len(issues) == 1
        assert issues[0].severity == Severity.ALLOW

    def test_issue_details_contain_field_info(self) -> None:
        rules = ComparabilityRules.create()
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_id="census_2022"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_id="survey_2023"
        )
        issues = rules.check_compatibility([m1, m2])

        assert len(issues) == 1
        details = issues[0].details
        assert details["field"] == "methodology_id"
        assert details["metric_1"] == "metric1"
        assert details["metric_2"] == "metric2"
        assert details["value_1"] == "census_2022"
        assert details["value_2"] == "survey_2023"
        assert details["severity_label"] == "warning"

    def test_issue_details_severity_label_for_error(self) -> None:
        rules = ComparabilityRules.create(default_policy=ComparabilityPolicy.FORBID)
        m1 = self._create_metric_with_comparability(
            "metric1", methodology_id="census_2022"
        )
        m2 = self._create_metric_with_comparability(
            "metric2", methodology_id="survey_2023"
        )
        issues = rules.check_compatibility([m1, m2])

        assert issues[0].details["severity_label"] == "error"
