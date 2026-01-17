"""Application layer exceptions."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base application exception."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class DataProductNotFoundError(ApplicationError):
    """Raised when a data product is not found."""

    def __init__(self, data_product_id: str, message: str | None = None) -> None:
        self.data_product_id = data_product_id
        msg = message or f"Data product not found: {data_product_id}"
        super().__init__("DATA_PRODUCT_NOT_FOUND", msg)


class VariableNotFoundError(ApplicationError):
    """Raised when a variable is not found."""

    def __init__(
        self, variable_name: str, data_product_id: str, message: str | None = None
    ) -> None:
        self.variable_name = variable_name
        self.data_product_id = data_product_id
        msg = (
            message
            or f"Variable '{variable_name}' not found in data product '{data_product_id}'"
        )
        super().__init__("VARIABLE_NOT_FOUND", msg)


class QueryNotFoundError(ApplicationError):
    """Raised when a query is not found."""

    def __init__(self, query_id: str, message: str | None = None) -> None:
        self.query_id = query_id
        msg = message or f"Query not found: {query_id}"
        super().__init__("QUERY_NOT_FOUND", msg)


class QueryNotExecutableError(ApplicationError):
    """Raised when a query cannot be executed."""

    def __init__(self, query_id: str, reason: str, message: str | None = None) -> None:
        self.query_id = query_id
        self.reason = reason
        msg = message or f"Query '{query_id}' cannot be executed: {reason}"
        super().__init__("QUERY_NOT_EXECUTABLE", msg)


class StudyNotFoundError(ApplicationError):
    """Raised when a study is not found."""

    def __init__(self, study_id: str, message: str | None = None) -> None:
        self.study_id = study_id
        msg = message or f"Study not found: {study_id}"
        super().__init__("STUDY_NOT_FOUND", msg)


class DatasetNotFoundError(ApplicationError):
    """Raised when a dataset is not found."""

    def __init__(self, dataset_id: str, message: str | None = None) -> None:
        self.dataset_id = dataset_id
        msg = message or f"Dataset not found: {dataset_id}"
        super().__init__("DATASET_NOT_FOUND", msg)
