"""Use cases for direct domain management.

Provides use cases for directly setting and deprecating ColumnDomains,
bypassing the proposal workflow. Used for data migrations, administrative
corrections, and other scenarios where proposal review is not needed.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol
from uuid import UUID

from invariant.domain.model.ids import ConceptId
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
    Grain,
    MeasurementKind,
    ReferenceBinding,
    ValueSpace,
)

# Exceptions


class DomainNotFoundError(Exception):
    """Raised when a domain cannot be found."""

    def __init__(self, domain_id: str) -> None:
        self.domain_id = domain_id
        super().__init__(f"Domain not found: {domain_id}")


class InvalidValueSpaceError(Exception):
    """Raised when an invalid value space string is provided."""

    def __init__(self, value_space: str) -> None:
        self.value_space = value_space
        valid_values = [vs.name for vs in ValueSpace]
        super().__init__(
            f"Invalid value space: {value_space}. Valid values: {valid_values}"
        )


class InvalidMeasurementKindError(Exception):
    """Raised when an invalid measurement kind string is provided."""

    def __init__(self, measurement_kind: str) -> None:
        self.measurement_kind = measurement_kind
        valid_values = [mk.name for mk in MeasurementKind]
        super().__init__(
            f"Invalid measurement kind: {measurement_kind}. Valid values: {valid_values}"
        )


# Port interfaces


class ColumnDomainStore(Protocol):
    """Protocol for accessing ColumnDomain entities."""

    def get(self, domain_id: str) -> ColumnDomain | None:
        """Get a domain by ID."""
        ...

    def save(self, domain: ColumnDomain) -> None:
        """Save a domain."""
        ...


# Request DTOs


@dataclass(frozen=True)
class SetDomainRequest:
    """Request to directly set a column domain.

    Bypasses the proposal workflow for administrative use cases
    such as data migration or corrections.

    Frozen DTO for set domain use case.
    """

    variable_id: str
    concept_id: str | None
    universe_id: str | None
    value_space: str
    measurement_kind: str
    reference_system_id: str | None
    reference_version_id: str | None
    grain_keys: tuple[str, ...] | None
    set_by: str
    reason: str


@dataclass(frozen=True)
class DeprecateDomainRequest:
    """Request to deprecate a column domain.

    Frozen DTO for deprecate domain use case.
    """

    domain_id: str
    deprecated_by: str
    reason: str


# Use cases


@dataclass
class SetDomainUseCase:
    """Use case for directly setting a column domain.

    Creates a confirmed ColumnDomain bypassing the proposal workflow.
    Used for data migrations, administrative corrections, and other
    scenarios where proposal review is not needed.
    """

    domain_store: ColumnDomainStore

    def execute(self, request: SetDomainRequest) -> ColumnDomain:
        """Set a domain directly without proposal workflow.

        Args:
            request: The set domain request with all required fields.

        Returns:
            The created ColumnDomain.

        Raises:
            InvalidValueSpaceError: If the value space string is invalid.
            InvalidMeasurementKindError: If the measurement kind string is invalid.
        """
        # Map string to ValueSpace enum
        try:
            value_space = ValueSpace[request.value_space]
        except KeyError:
            raise InvalidValueSpaceError(request.value_space) from None

        # Map string to MeasurementKind enum
        try:
            measurement_kind = MeasurementKind[request.measurement_kind]
        except KeyError:
            raise InvalidMeasurementKindError(request.measurement_kind) from None

        # Create ReferenceBinding if both IDs provided
        reference_binding: ReferenceBinding | None = None
        if request.reference_system_id and request.reference_version_id:
            reference_binding = ReferenceBinding(
                system_id=request.reference_system_id,
                version_id=request.reference_version_id,
            )

        # Create Grain if keys provided
        grain: Grain | None = None
        if request.grain_keys:
            grain = Grain(keys=request.grain_keys)

        # Create concept_id from string (expects UUID format)
        concept_id: ConceptId | None = None
        if request.concept_id:
            concept_id = ConceptId(UUID(request.concept_id))

        # Create confirmed domain
        now = datetime.now()
        domain = ColumnDomain(
            id=ColumnDomainId.create(),
            variable_id=request.variable_id,
            concept_id=concept_id,
            universe_id=request.universe_id,
            value_space=value_space,
            measurement_kind=measurement_kind,
            reference_binding=reference_binding,
            grain=grain,
            status=DomainStatus.CONFIRMED,
            confirmed_at=now,
            confirmed_by=request.set_by,
        )

        # Save domain
        self.domain_store.save(domain)

        return domain


@dataclass
class DeprecateDomainUseCase:
    """Use case for deprecating a column domain.

    Updates an existing domain's status to DEPRECATED.
    """

    domain_store: ColumnDomainStore

    def execute(self, request: DeprecateDomainRequest) -> None:
        """Deprecate an existing domain.

        Args:
            request: The deprecation request with domain ID and reason.

        Raises:
            DomainNotFoundError: If the domain doesn't exist.
        """
        # Get existing domain
        domain = self.domain_store.get(request.domain_id)
        if domain is None:
            raise DomainNotFoundError(request.domain_id)

        # Create deprecated domain (ColumnDomain is frozen, so we use replace)
        deprecated_domain = replace(domain, status=DomainStatus.DEPRECATED)

        # Save the updated domain
        self.domain_store.save(deprecated_domain)
