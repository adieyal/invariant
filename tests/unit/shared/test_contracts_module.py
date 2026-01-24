"""Tests for contracts module structure and imports."""

import ast
from pathlib import Path


class TestContractsModule:
    """Tests for the contracts module."""

    def test_contracts_module_importable(self) -> None:
        """Contracts module can be imported."""
        from invariant.shared import contracts

        assert contracts is not None

    def test_contracts_has_no_component_dependencies(self) -> None:
        """Contracts module doesn't import from components."""
        # Components that contracts should NOT depend on
        forbidden_imports = {
            "invariant.domain",
            "invariant.application",
            "invariant.catalog",
            "invariant.query",
        }

        # Find the contracts __init__.py
        contracts_init = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "invariant"
            / "shared"
            / "contracts"
            / "__init__.py"
        )

        assert contracts_init.exists(), f"Expected {contracts_init} to exist"

        source = contracts_init.read_text()
        tree = ast.parse(source)

        # Collect all imports
        found_imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found_imports.add(node.module)

        # Check for forbidden imports
        violations = found_imports & forbidden_imports
        assert not violations, (
            f"Contracts module imports forbidden components: {violations}"
        )

    def test_shared_module_importable(self) -> None:
        """Shared module can be imported."""
        from invariant import shared

        assert shared is not None
