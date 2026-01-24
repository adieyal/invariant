"""Identity application use cases.

Use cases orchestrate domain logic and coordinate with ports.
"""

from invariant.identity.application.ports.column_domain_store import (
    ColumnDomainProposalStore,
    ColumnDomainStore,
)
from invariant.identity.application.use_cases.adjudicate_proposal import (
    AcceptProposalRequest,
    AcceptProposalUseCase,
    ProposalNotFoundError,
    ProposalNotPendingError,
    RejectProposalRequest,
    RejectProposalUseCase,
    RequestRefinementRequest,
    RequestRefinementUseCase,
)
from invariant.identity.application.use_cases.assess_compatibility import (
    AssessCompatibilityRequest,
    AssessCompatibilityResult,
    AssessCompatibilityUseCase,
    CompatibilityResultDTO,
)
from invariant.identity.application.use_cases.manage_domain import (
    ColumnDomainDTO,
    DeprecateDomainRequest,
    DeprecateDomainUseCase,
    DomainNotFoundError,
    InvalidMeasurementKindError,
    InvalidValueSpaceError,
    SetDomainRequest,
    SetDomainUseCase,
)

__all__ = [
    "AcceptProposalRequest",
    "AcceptProposalUseCase",
    "AssessCompatibilityRequest",
    "AssessCompatibilityResult",
    "AssessCompatibilityUseCase",
    "ColumnDomainDTO",
    "ColumnDomainProposalStore",
    "ColumnDomainStore",
    "CompatibilityResultDTO",
    "DeprecateDomainRequest",
    "DeprecateDomainUseCase",
    "DomainNotFoundError",
    "InvalidMeasurementKindError",
    "InvalidValueSpaceError",
    "ProposalNotFoundError",
    "ProposalNotPendingError",
    "RejectProposalRequest",
    "RejectProposalUseCase",
    "RequestRefinementRequest",
    "RequestRefinementUseCase",
    "SetDomainRequest",
    "SetDomainUseCase",
]
