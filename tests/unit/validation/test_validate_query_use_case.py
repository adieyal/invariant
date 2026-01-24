"""Tests for ValidateQueryUseCase in the Validation component."""


def test_validate_query_use_case_importable():
    """ValidateQueryUseCase can be imported from validation component."""
    from invariant.validation.application.use_cases import ValidateQueryUseCase

    assert ValidateQueryUseCase is not None


def test_backward_compatible_import():
    """ValidateQueryUseCase can still be imported from old location."""
    from invariant.application.use_cases.validate_query import ValidateQueryUseCase

    assert ValidateQueryUseCase is not None


def test_both_imports_same_class():
    """Both import paths reference the same class."""
    from invariant.application.use_cases.validate_query import (
        ValidateQueryUseCase as OldImport,
    )
    from invariant.validation.application.use_cases import (
        ValidateQueryUseCase as NewImport,
    )

    assert OldImport is NewImport
