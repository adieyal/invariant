"""Boundary verification tests for the Invariant Analytics Kernel.

US-P7-005: Final boundary verification.

These tests verify that component boundaries are correctly enforced:
1. Import linter passes (no boundary violations)
2. Components communicate via contracts, not internals
3. No circular imports between components
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

# Root of the project
# tests/unit/test_boundary_verification.py -> parent.parent.parent = project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
INVARIANT_ROOT = SRC_ROOT / "invariant"


class TestImportLinter:
    """Tests that verify import linter configuration and compliance."""

    def test_import_linter_passes(self) -> None:
        """Import linter shows no boundary violations.

        Runs lint-imports and verifies that all contracts are kept.
        This is the primary boundary enforcement mechanism.
        """
        env = {"PYTHONPATH": str(SRC_ROOT)}
        env.update(
            {k: v for k, v in __import__("os").environ.items() if k != "PYTHONPATH"}
        )

        result = subprocess.run(
            ["lint-imports", "--config", str(PROJECT_ROOT / ".importlinter")],
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

        # Parse output to check for broken contracts
        output = result.stdout + result.stderr
        if "broken" in output.lower() and result.returncode != 0:
            pytest.fail(f"Import linter found boundary violations:\n{output}")

        assert result.returncode == 0, f"Import linter failed:\n{output}"

    def test_importlinter_config_exists(self) -> None:
        """Import linter configuration file exists."""
        config_path = PROJECT_ROOT / ".importlinter"
        assert config_path.exists(), f"Missing .importlinter at {config_path}"

    def test_importlinter_covers_all_components(self) -> None:
        """Import linter configuration covers all components.

        Verifies that each component has layer contracts defined.
        """
        config_path = PROJECT_ROOT / ".importlinter"
        config_content = config_path.read_text()

        components = [
            "catalog",
            "identity",
            "semantic",
            "query",
            "validation",
            "reference",
        ]
        for component in components:
            # Check for layer contract
            layer_contract = f"[importlinter:contract:{component}-layers]"
            assert (
                layer_contract in config_content
                or f"containers =\n    invariant.{component}" in config_content
            ), f"Missing layer contract for component: {component}"


class TestComponentContracts:
    """Tests that verify components use contracts for communication."""

    def _get_python_files(self, directory: Path) -> Iterator[Path]:
        """Yield all Python files in a directory."""
        for path in directory.rglob("*.py"):
            if "__pycache__" not in str(path):
                yield path

    def _get_imports_from_file(self, file_path: Path) -> list[str]:
        """Extract all imports from a Python file."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def test_shared_contracts_are_pure(self) -> None:
        """Shared contracts have no dependencies on components.

        The shared.contracts module must be completely pure and not
        depend on any component internals.
        """
        contracts_dir = INVARIANT_ROOT / "shared" / "contracts"
        if not contracts_dir.exists():
            pytest.skip("shared/contracts directory not found")

        forbidden_prefixes = [
            "invariant.catalog",
            "invariant.identity",
            "invariant.semantic",
            "invariant.query",
            "invariant.validation",
            "invariant.reference",
            "invariant.kernel",
            "invariant.domain",
            "invariant.application",
        ]

        violations = []
        for py_file in self._get_python_files(contracts_dir):
            imports = self._get_imports_from_file(py_file)
            for imp in imports:
                for prefix in forbidden_prefixes:
                    if imp.startswith(prefix):
                        violations.append(
                            f"{py_file.relative_to(PROJECT_ROOT)}: imports {imp}"
                        )

        if violations:
            pytest.fail(
                "Shared contracts have forbidden dependencies:\n"
                + "\n".join(violations)
            )

    def test_kernel_uses_contracts_not_internals(self) -> None:
        """Kernel facade uses shared contracts, not component internals.

        The kernel should depend on:
        - invariant.shared.contracts (allowed)
        - invariant.domain.model.ids (allowed - central IDs)
        - invariant.application.dto (allowed - DTOs)

        Not on:
        - invariant.{component}.domain (forbidden)
        - invariant.{component}.application (forbidden)
        """
        kernel_dir = INVARIANT_ROOT / "kernel"
        if not kernel_dir.exists():
            pytest.skip("kernel directory not found")

        # These are forbidden direct imports from component internals
        forbidden_patterns = [
            "invariant.catalog.domain",
            "invariant.catalog.application",
            "invariant.identity.domain",
            "invariant.identity.application",
            "invariant.semantic.domain",
            "invariant.semantic.application",
            "invariant.query.domain",
            "invariant.query.application",
            "invariant.validation.domain",
            "invariant.validation.application",
            "invariant.reference.domain",
            "invariant.reference.application",
        ]

        violations = []
        for py_file in self._get_python_files(kernel_dir):
            imports = self._get_imports_from_file(py_file)
            for imp in imports:
                for pattern in forbidden_patterns:
                    if imp.startswith(pattern):
                        violations.append(
                            f"{py_file.relative_to(PROJECT_ROOT)}: imports {imp}"
                        )

        if violations:
            pytest.fail(
                "Kernel has forbidden direct component imports:\n"
                + "\n".join(violations)
            )

    def test_components_have_clean_architecture_layers(self) -> None:
        """Each component follows Clean Architecture with domain and application layers.

        Verifies that each component has the expected structure:
        - domain/ (entities, value objects, services)
        - application/ (ports, services, use cases)
        """
        components = [
            "catalog",
            "identity",
            "semantic",
            "query",
            "validation",
            "reference",
        ]

        missing_structure = []
        for component in components:
            component_dir = INVARIANT_ROOT / component
            if not component_dir.exists():
                continue

            domain_dir = component_dir / "domain"
            application_dir = component_dir / "application"

            if not domain_dir.exists():
                missing_structure.append(f"{component}: missing domain/ directory")
            if not application_dir.exists():
                missing_structure.append(f"{component}: missing application/ directory")

        if missing_structure:
            pytest.fail(
                "Components missing Clean Architecture structure:\n"
                + "\n".join(missing_structure)
            )


class TestNoCircularImports:
    """Tests that verify no circular imports exist between components."""

    def test_no_circular_component_imports(self) -> None:
        """No circular imports between components.

        Tests that each component can be imported without circular import errors.
        """
        components = [
            "invariant.catalog",
            "invariant.identity",
            "invariant.semantic",
            "invariant.query",
            "invariant.validation",
            "invariant.reference",
            "invariant.kernel",
        ]

        errors = []
        for component in components:
            try:
                # Use subprocess to avoid polluting test process
                result = subprocess.run(
                    [sys.executable, "-c", f"import {component}"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(PROJECT_ROOT),
                    env={"PYTHONPATH": str(SRC_ROOT), **__import__("os").environ},
                )
                if result.returncode != 0:
                    errors.append(f"{component}: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                errors.append(
                    f"{component}: import timed out (possible circular import)"
                )

        if errors:
            pytest.fail("Import errors detected:\n" + "\n".join(errors))

    def test_shared_contracts_importable(self) -> None:
        """Shared contracts module can be imported independently."""
        result = subprocess.run(
            [sys.executable, "-c", "import invariant.shared.contracts"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
            env={"PYTHONPATH": str(SRC_ROOT), **__import__("os").environ},
        )
        assert result.returncode == 0, (
            f"Failed to import shared.contracts: {result.stderr}"
        )


class TestComponentPublicAPI:
    """Tests that verify components expose proper public APIs."""

    def test_components_export_via_init(self) -> None:
        """Components export their public API via __init__.py.

        Each component should have an __init__.py that exposes the
        public interface, allowing imports like:
            from invariant.catalog import CatalogStore
        """
        components = [
            "catalog",
            "identity",
            "semantic",
            "query",
            "validation",
            "reference",
            "kernel",
        ]

        missing_init = []
        for component in components:
            init_file = INVARIANT_ROOT / component / "__init__.py"
            if not init_file.exists():
                missing_init.append(component)

        if missing_init:
            pytest.fail(f"Components missing __init__.py: {missing_init}")

    def test_kernel_facade_importable(self) -> None:
        """InvariantKernel facade can be imported from kernel module."""
        result = subprocess.run(
            [sys.executable, "-c", "from invariant.kernel import InvariantKernel"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
            env={"PYTHONPATH": str(SRC_ROOT), **__import__("os").environ},
        )
        assert result.returncode == 0, (
            f"Failed to import InvariantKernel: {result.stderr}"
        )
