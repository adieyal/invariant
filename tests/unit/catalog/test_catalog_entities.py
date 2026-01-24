"""Tests for catalog entities.

These tests verify that core catalog entities are importable from
the catalog component and maintain backward compatibility with
the original domain/model imports.
"""


class TestCatalogEntityImports:
    """Test that entities are importable from invariant.catalog."""

    def test_study_importable_from_catalog(self):
        """Study can be imported from catalog."""
        from invariant.catalog import Study

        assert Study is not None

    def test_dataset_importable_from_catalog(self):
        """Dataset can be imported from catalog."""
        from invariant.catalog import Dataset

        assert Dataset is not None

    def test_data_product_importable_from_catalog(self):
        """DataProduct can be imported from catalog."""
        from invariant.catalog import DataProduct

        assert DataProduct is not None

    def test_variable_importable_from_catalog(self):
        """Variable can be imported from catalog."""
        from invariant.catalog import Variable

        assert Variable is not None


class TestBackwardCompatibleImports:
    """Test that old import paths still work for backward compatibility."""

    def test_study_backward_compatible_import(self):
        """Study can still be imported from domain/model/study."""
        from invariant.domain.model.study import Study

        assert Study is not None

    def test_dataset_backward_compatible_import(self):
        """Dataset can still be imported from domain/model/dataset."""
        from invariant.domain.model.dataset import Dataset

        assert Dataset is not None

    def test_data_product_backward_compatible_import(self):
        """DataProduct can still be imported from domain/model/data_product."""
        from invariant.domain.model.data_product import DataProduct

        assert DataProduct is not None

    def test_variable_backward_compatible_import(self):
        """Variable can still be imported from domain/model/variable."""
        from invariant.domain.model.variable import Variable

        assert Variable is not None


class TestEntityIdentity:
    """Test that catalog and domain/model imports refer to the same classes."""

    def test_study_is_same_class(self):
        """Study from catalog and domain/model are the same class."""
        from invariant.catalog import Study as CatalogStudy
        from invariant.domain.model.study import Study as DomainStudy

        assert CatalogStudy is DomainStudy

    def test_dataset_is_same_class(self):
        """Dataset from catalog and domain/model are the same class."""
        from invariant.catalog import Dataset as CatalogDataset
        from invariant.domain.model.dataset import Dataset as DomainDataset

        assert CatalogDataset is DomainDataset

    def test_data_product_is_same_class(self):
        """DataProduct from catalog and domain/model are the same class."""
        from invariant.catalog import DataProduct as CatalogDataProduct
        from invariant.domain.model.data_product import DataProduct as DomainDataProduct

        assert CatalogDataProduct is DomainDataProduct

    def test_variable_is_same_class(self):
        """Variable from catalog and domain/model are the same class."""
        from invariant.catalog import Variable as CatalogVariable
        from invariant.domain.model.variable import Variable as DomainVariable

        assert CatalogVariable is DomainVariable
