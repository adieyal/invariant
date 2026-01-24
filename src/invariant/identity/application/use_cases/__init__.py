"""Identity application use cases.

Use cases orchestrate domain logic and coordinate with ports.
"""

from invariant.identity.application.use_cases.adjudicate_proposal import (
    AcceptProposalRequest,
    AcceptProposalUseCase,
    ColumnDomainProposalStore,
    ColumnDomainStore,
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
)
from invariant.identity.application.use_cases.manage_domain import (
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
    "ColumnDomainProposalStore",
    "ColumnDomainStore",
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
