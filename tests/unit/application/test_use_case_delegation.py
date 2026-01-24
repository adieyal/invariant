"""Tests for use case delegation to kernel facade.

US-P7-004: Remove orchestration from old use cases.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest

from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.dto.results_dto import QueryResultDTO, ResultMetadataDTO
from invariant.application.use_cases.execute_query import ExecuteQueryUseCase

# === Fake Kernel Implementation ===


@dataclass
class FakeKernel:
    """Fake kernel for testing delegation.

    Tracks calls to run_query and returns a configurable result.
    """

    _run_query_calls: list[QueryRequest] = None
    _result: QueryResultDTO | None = None

    def __post_init__(self) -> None:
        if self._run_query_calls is None:
            self._run_query_calls = []

    def run_query(self, request: QueryRequest) -> QueryResultDTO:
        """Record the call and return configured result."""
        self._run_query_calls.append(request)
        if self._result is not None:
            return self._result
        return QueryResultDTO(
            query_id=str(uuid4()),
            columns=[],
            rows=[],
            disclosures=[],
            metadata=ResultMetadataDTO(
                total_rows=0,
                execution_time_ms=0,
                data_sources=(),
                reference_periods=(),
                suppressed_count=0,
            ),
        )

    def set_result(self, result: QueryResultDTO) -> None:
        """Configure the result to return."""
        self._result = result

    @property
    def call_count(self) -> int:
        """Return the number of calls to run_query."""
        return len(self._run_query_calls)

    @property
    def last_request(self) -> QueryRequest | None:
        """Return the last request passed to run_query."""
        if self._run_query_calls:
            return self._run_query_calls[-1]
        return None


# === Tests for Delegation ===


class TestExecuteQueryDelegation:
    """Tests that ExecuteQueryUseCase can delegate to kernel.run_query()."""

    @pytest.fixture
    def fake_kernel(self) -> FakeKernel:
        """Create a fake kernel for testing."""
        return FakeKernel()

    @pytest.fixture
    def simple_request(self) -> QueryRequest:
        """Create a simple query request for testing."""
        return QueryRequest(
            intent="TABLE",
            selections=[
                DataProductSelectionRequest(
                    data_product_id=str(uuid4()),
                    dimensions=["region"],
                    metrics=[MetricRequest(variable="population", aggregation="SUM")],
                )
            ],
        )

    def test_execute_query_delegates_to_kernel(
        self,
        fake_kernel: FakeKernel,
        simple_request: QueryRequest,
    ) -> None:
        """ExecuteQueryUseCase delegates to kernel.run_query().

        When a kernel is provided, the use case should delegate all
        orchestration to the kernel rather than doing it internally.
        """
        # Configure expected result
        expected_result = QueryResultDTO(
            query_id="kernel-generated-id",
            columns=[],
            rows=[{"region": "North", "population": 1000}],
            disclosures=[],
            metadata=ResultMetadataDTO(
                total_rows=1,
                execution_time_ms=42,
                data_sources=("census",),
                reference_periods=(),
                suppressed_count=0,
            ),
        )
        fake_kernel.set_result(expected_result)

        # Create use case with kernel
        use_case = ExecuteQueryUseCase(kernel=fake_kernel)

        # Execute
        result = use_case.execute(simple_request)

        # Verify delegation occurred
        assert fake_kernel.call_count == 1
        assert fake_kernel.last_request == simple_request
        assert result == expected_result

    def test_execute_query_delegates_with_query_id(
        self,
        fake_kernel: FakeKernel,
        simple_request: QueryRequest,
    ) -> None:
        """ExecuteQueryUseCase passes query_id to kernel if provided.

        Note: The kernel.run_query() currently generates its own ID,
        but the use case should be prepared to handle this gracefully.
        """
        use_case = ExecuteQueryUseCase(kernel=fake_kernel)

        # Execute with custom query_id
        use_case.execute(simple_request, query_id="custom-id")

        # Delegation should still occur
        assert fake_kernel.call_count == 1


class TestNoCrossComponentImports:
    """Tests that use cases don't import directly from other component internals.

    Cross-component imports (e.g., application use cases importing directly from
    validation.application.ports) indicate tight coupling that should go through
    the kernel facade instead.
    """

    def test_no_direct_cross_component_imports(self) -> None:
        """Use cases don't import directly from other component internals.

        This test inspects the AST of use case modules to detect imports
        from other components (validation, catalog, identity, semantic, etc.)
        that should instead flow through the kernel facade.

        Allowed imports:
        - invariant.application.* (same component)
        - invariant.domain.* (domain layer)
        - invariant.kernel.* (kernel facade)
        - invariant.shared.* (shared contracts)

        Disallowed imports (should use kernel instead):
        - invariant.validation.application.* (validation component internals)
        - invariant.catalog.application.* (catalog component internals)
        - invariant.identity.application.* (identity component internals)
        - invariant.semantic.application.* (semantic component internals)
        """
        use_cases_dir = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "invariant"
            / "application"
            / "use_cases"
        )

        # Known violations that are being migrated (add file names here as they get fixed)
        # Once all are migrated, this list should be empty
        known_violations: dict[str, set[str]] = {
            # execute_query.py has legacy validation imports - tracked for migration
            "execute_query.py": {
                "invariant.validation.application.ports",
            },
            # acknowledge_issues.py imports from validation ports for AuditLog
            "acknowledge_issues.py": {
                "invariant.validation.application.ports",
            },
            # validate_query.py is a deprecated re-export shim for backward compat
            "validate_query.py": {
                "invariant.validation.application.use_cases.validate_query",
            },
        }

        # Cross-component patterns that indicate tight coupling
        cross_component_patterns = [
            "invariant.validation.application",
            "invariant.catalog.application",
            "invariant.identity.application",
            "invariant.semantic.application",
        ]

        violations: dict[str, list[str]] = {}

        for py_file in use_cases_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            source = py_file.read_text()
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            file_violations: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for pattern in cross_component_patterns:
                            if alias.name.startswith(pattern):
                                file_violations.append(alias.name)

                elif isinstance(node, ast.ImportFrom) and node.module:
                    for pattern in cross_component_patterns:
                        if node.module.startswith(pattern):
                            file_violations.append(node.module)

            # Filter out known violations
            known_for_file = known_violations.get(py_file.name, set())
            unexpected_violations = [
                v for v in file_violations if v not in known_for_file
            ]

            if unexpected_violations:
                violations[py_file.name] = unexpected_violations

        if violations:
            msg_parts = ["Unexpected cross-component imports detected:\n"]
            for file_name, imports in violations.items():
                msg_parts.append(f"  {file_name}:")
                for imp in imports:
                    msg_parts.append(f"    - {imp}")
            msg_parts.append(
                "\n\nUse cases should coordinate through the kernel facade, "
                "not import directly from other component internals."
            )
            pytest.fail("\n".join(msg_parts))

    def test_execute_query_can_use_kernel_facade(self) -> None:
        """ExecuteQueryUseCase accepts kernel parameter for delegation.

        This test verifies the use case has been updated to support
        kernel-based orchestration.
        """
        # Verify ExecuteQueryUseCase can be instantiated with a kernel
        # This is a structural test - the actual delegation is tested above
        import inspect

        sig = inspect.signature(ExecuteQueryUseCase)

        # The kernel parameter should exist (may be optional for backward compat)
        param_names = list(sig.parameters.keys())
        assert "kernel" in param_names, (
            "ExecuteQueryUseCase should accept a 'kernel' parameter for delegation. "
            f"Found parameters: {param_names}"
        )
