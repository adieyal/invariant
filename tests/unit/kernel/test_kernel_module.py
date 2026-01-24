"""Tests for kernel module imports.

US-P7-001: Create Kernel Facade structure using TDD.
"""


def test_kernel_module_importable():
    """Test that the kernel module is importable from invariant."""
    from invariant import kernel

    assert kernel is not None


def test_invariant_kernel_importable():
    """Test that InvariantKernel is importable from the kernel module."""
    from invariant.kernel import InvariantKernel

    assert InvariantKernel is not None


def test_kernel_facade_importable():
    """Test that InvariantKernel is importable from facade module."""
    from invariant.kernel.facade import InvariantKernel

    assert InvariantKernel is not None


def test_invariant_kernel_is_dataclass():
    """Test that InvariantKernel is a dataclass."""
    from dataclasses import fields

    from invariant.kernel import InvariantKernel

    # If it's a dataclass, fields() will work
    kernel_fields = fields(InvariantKernel)
    assert len(kernel_fields) > 0


def test_invariant_kernel_has_required_providers():
    """Test that InvariantKernel has the required provider fields."""
    from dataclasses import fields

    from invariant.kernel import InvariantKernel

    field_names = {f.name for f in fields(InvariantKernel)}

    # Required providers from the spec
    expected_providers = {
        "catalog",
        "identity",
        "semantic",
        "query",
        "validation",
        "reference",
    }

    assert expected_providers.issubset(field_names), (
        f"Missing providers: {expected_providers - field_names}"
    )
