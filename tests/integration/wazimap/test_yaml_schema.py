"""Integration tests for YAML schema validation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from invariant_contrib.wazimap.infrastructure.yaml_schema import (
    SchemaError,
    SchemaErrorSeverity,
    SchemaValidator,
    validate_assets,
)

# Get fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
INVALID_FIXTURES_DIR = Path(__file__).parent / "fixtures_invalid"


class TestValidAssets:
    """Tests that valid assets pass validation."""

    def test_valid_assets_have_no_errors(self) -> None:
        """Valid assets should pass with no errors."""
        errors = validate_assets(FIXTURES_DIR)

        # Filter to only errors (warnings are acceptable for cross-references)
        error_list = [e for e in errors if e.severity == SchemaErrorSeverity.ERROR]

        assert len(error_list) == 0, f"Unexpected errors: {error_list}"

    def test_schema_validator_collects_known_assets(self) -> None:
        """Validator should collect known asset names during validation."""
        validator = SchemaValidator()
        validator.validate_asset_directory(FIXTURES_DIR)

        assert "population" in validator.known_datasets
        assert "geography" in validator.known_datasets
        assert "age_group" in validator.known_dimensions
        assert "south_africa" in validator.known_geo_hierarchies
        assert "total_population" in validator.known_metrics
        assert "land_area" in validator.known_metrics
        assert "population_density" in validator.known_metrics


class TestInvalidAssets:
    """Tests that invalid assets are detected."""

    def test_missing_required_field_detected(self) -> None:
        """Missing required fields should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for missing physical_ref
        missing_errors = [
            e
            for e in errors
            if "physical_ref" in e.field_path and "missing" in e.message
        ]
        assert len(missing_errors) > 0, "Should detect missing physical_ref"

    def test_invalid_enum_value_detected(self) -> None:
        """Invalid enum values should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for invalid kind
        kind_errors = [
            e for e in errors if e.field_path == "kind" and "INVALID_KIND" in e.message
        ]
        assert len(kind_errors) > 0, "Should detect invalid kind enum"

    def test_wrong_field_type_detected(self) -> None:
        """Wrong field types should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for wrong type
        type_errors = [
            e for e in errors if e.field_path == "name" and "expected str" in e.message
        ]
        assert len(type_errors) > 0, "Should detect wrong field type"

    def test_invalid_yaml_syntax_detected(self) -> None:
        """Invalid YAML syntax should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for invalid YAML
        yaml_errors = [e for e in errors if "Invalid YAML syntax" in e.message]
        assert len(yaml_errors) > 0, "Should detect invalid YAML syntax"

    def test_empty_attributes_detected(self) -> None:
        """Empty attributes in dimension should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for empty attributes
        attr_errors = [
            e
            for e in errors
            if e.field_path == "attributes" and "must not be empty" in e.message
        ]
        assert len(attr_errors) > 0, "Should detect empty attributes"

    def test_invalid_data_type_detected(self) -> None:
        """Invalid data type in dimension attribute should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for invalid data type
        data_type_errors = [
            e
            for e in errors
            if "data_type" in e.field_path and "UNKNOWN_TYPE" in e.message
        ]
        assert len(data_type_errors) > 0, "Should detect invalid data_type"

    def test_invalid_parent_level_reference_detected(self) -> None:
        """Invalid parent level reference should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for invalid parent level
        parent_errors = [
            e
            for e in errors
            if "parent_level" in e.field_path and "unknown_level" in e.message
        ]
        assert len(parent_errors) > 0, "Should detect invalid parent level reference"

    def test_invalid_aggregation_function_detected(self) -> None:
        """Invalid aggregation function should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for invalid agg
        agg_errors = [
            e for e in errors if "agg" in e.field_path and "MEDIAN" in e.message
        ]
        assert len(agg_errors) > 0, "Should detect invalid aggregation function"

    def test_empty_deps_detected(self) -> None:
        """Empty deps in derived metric should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for empty deps
        deps_errors = [
            e
            for e in errors
            if e.field_path == "spec.deps" and "must not be empty" in e.message
        ]
        assert len(deps_errors) > 0, "Should detect empty deps"

    def test_empty_metrics_list_detected(self) -> None:
        """Empty metrics list in materialization should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for empty metrics
        metrics_errors = [
            e
            for e in errors
            if e.field_path == "metrics" and "must not be empty" in e.message
        ]
        assert len(metrics_errors) > 0, "Should detect empty metrics list"

    def test_interval_without_minutes_detected(self) -> None:
        """INTERVAL strategy without interval_minutes should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for missing interval_minutes
        interval_errors = [
            e
            for e in errors
            if "interval_minutes" in e.field_path
            and "required when strategy is INTERVAL" in e.message
        ]
        assert len(interval_errors) > 0, (
            "Should detect missing interval_minutes for INTERVAL strategy"
        )

    def test_invalid_comparability_policy_detected(self) -> None:
        """Invalid comparability policy should be detected."""
        errors = validate_assets(INVALID_FIXTURES_DIR)

        # Find the error for invalid policy
        policy_errors = [
            e
            for e in errors
            if "default_policy" in e.field_path and "UNKNOWN_POLICY" in e.message
        ]
        assert len(policy_errors) > 0, "Should detect invalid comparability policy"


class TestSchemaError:
    """Tests for SchemaError class."""

    def test_error_str_format(self) -> None:
        """SchemaError string representation should be formatted correctly."""
        error = SchemaError(
            file_path=Path("/path/to/file.yml"),
            field_path="some.field",
            message="Something is wrong",
            severity=SchemaErrorSeverity.ERROR,
        )

        result = str(error)

        assert "[ERROR]" in result
        assert "/path/to/file.yml" in result
        assert "some.field" in result
        assert "Something is wrong" in result

    def test_warning_str_format(self) -> None:
        """SchemaError warning string representation should be formatted correctly."""
        error = SchemaError(
            file_path=Path("/path/to/file.yml"),
            field_path="some.field",
            message="Something might be wrong",
            severity=SchemaErrorSeverity.WARNING,
        )

        result = str(error)

        assert "[WARNING]" in result

    def test_error_without_field_path(self) -> None:
        """SchemaError without field path should format correctly."""
        error = SchemaError(
            file_path=Path("/path/to/file.yml"),
            field_path="",
            message="File-level error",
        )

        result = str(error)

        # Should just show the file path without trailing colon
        assert "/path/to/file.yml:" in result
        assert "File-level error" in result


class TestSchemaValidator:
    """Tests for SchemaValidator class."""

    def test_nonexistent_assets_directory(self) -> None:
        """Validator should report error for nonexistent assets directory."""
        validator = SchemaValidator()
        errors = validator.validate_asset_directory(Path("/nonexistent/path"))

        assert len(errors) == 1
        assert "assets directory does not exist" in errors[0].message

    def test_cross_reference_warnings(self) -> None:
        """Validator should report warnings for cross-reference issues."""
        validator = SchemaValidator()
        errors = validator.validate_asset_directory(INVALID_FIXTURES_DIR)

        # Should have warnings for unknown dataset references
        unknown_warnings = [
            e
            for e in errors
            if e.severity == SchemaErrorSeverity.WARNING and "unknown" in e.message
        ]
        assert len(unknown_warnings) > 0, "Should have cross-reference warnings"


class TestCLIValidateAssets:
    """Tests for the CLI validate_assets tool."""

    def test_cli_module_can_be_imported(self) -> None:
        """CLI module should be importable."""
        from invariant_contrib.wazimap.tools import validate_assets as cli_module

        assert hasattr(cli_module, "main")

    def test_cli_main_with_valid_assets(self) -> None:
        """CLI should return 0 for valid assets."""
        import sys
        from unittest.mock import patch

        from invariant_contrib.wazimap.tools.validate_assets import main

        with patch.object(sys, "argv", ["validate_assets", str(FIXTURES_DIR)]):
            result = main()

        # Should succeed (0) or have warnings only (0)
        assert result == 0

    def test_cli_main_with_invalid_assets(self) -> None:
        """CLI should return 1 for invalid assets."""
        import sys
        from unittest.mock import patch

        from invariant_contrib.wazimap.tools.validate_assets import main

        with patch.object(sys, "argv", ["validate_assets", str(INVALID_FIXTURES_DIR)]):
            result = main()

        # Should fail with errors
        assert result == 1

    def test_cli_main_with_nonexistent_path(self) -> None:
        """CLI should return 2 for nonexistent path."""
        import sys
        from unittest.mock import patch

        from invariant_contrib.wazimap.tools.validate_assets import main

        with patch.object(sys, "argv", ["validate_assets", "/nonexistent/path"]):
            result = main()

        assert result == 2

    def test_cli_json_output(self, capsys: pytest.CaptureFixture) -> None:
        """CLI should output JSON when --json flag is used."""
        import json
        import sys
        from unittest.mock import patch

        from invariant_contrib.wazimap.tools.validate_assets import main

        with patch.object(
            sys, "argv", ["validate_assets", str(FIXTURES_DIR), "--json"]
        ):
            main()

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "path" in result
        assert "errors" in result
        assert "warnings" in result
        assert "summary" in result
