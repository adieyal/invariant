# Implementation Plan: Semantic Enforcement Layer

This plan covers the implementation of the semantic enforcement features determined to be in scope.

---

## Overview

**Goal:** Transform the kernel into a semantic execution engine where data meaning becomes machine-enforceable contracts.

**Scope:**
1. Executable semantics (claims/checks)
2. Runtime governance (validation gate)
3. Shift-left quality (semantic guarantees)
4. Dimensionality (attribution)
5. Impact analysis (meaning-level dependencies)
6. AI write-back safely (remediation actions)
7. Deeper context (docs + context slices + tool contracts)

**Approach:** Extend existing infrastructure. The current `Rule` protocol, `Issue`, `ValidationResult`, and port patterns provide a solid foundation. We extend rather than replace.

---

## Current State Summary

**Already Implemented:**
- Type-safe domain model with frozen dataclasses
- `Rule` protocol with `evaluate(plan, catalog) -> list[Issue]`
- `Issue` with severity, code, message, details, remediations
- `ValidationResult` with status computation
- `Validator` service running rules
- `CatalogSnapshot` for read-optimized validation
- Port-based architecture with fakes for testing
- `Remediation` as simple suggestion (action, label, required_fields)

**Key Files to Extend:**
- `domain/model/validation.py` - Issue, Remediation, ValidationResult
- `domain/services/validator.py` - Rule protocol, Validator
- `application/ports/catalog_store.py` - CatalogStore protocol
- `application/use_cases/validate_query.py` - ValidateQueryUseCase

---

## Phase 1: Domain Model Extensions (Foundation)

**Goal:** Add new value objects without breaking existing code.

### 1.1 Attribution Model

**File:** `src/new_wazi/domain/model/attribution.py` (NEW)

```python
@dataclass(frozen=True)
class AttributionDimension:
    variable_id: VariableId
    name: str

@dataclass(frozen=True)
class AttributionSlice:
    dimension: AttributionDimension
    value: str
    contribution_score: float  # 0.0 to 1.0
    row_count: int | None = None
    note: str | None = None

@dataclass(frozen=True)
class Attribution:
    slices: tuple[AttributionSlice, ...]
    method: str  # "exact" | "sampled" | "heuristic" | "unavailable"

    @classmethod
    def unavailable(cls) -> "Attribution":
        return cls(slices=(), method="unavailable")
```

**Tests:**
- Construction with valid slices
- `unavailable()` factory
- Immutability

### 1.2 Impact Model

**File:** `src/new_wazi/domain/model/impact.py` (NEW)

```python
class ImpactSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass(frozen=True)
class AffectedEntity:
    entity_type: str  # "DATASET" | "DATA_PRODUCT" | "INDICATOR" | "QUERY_PLAN"
    entity_id: str
    relation: str  # "uses_as_numerator" | "references" | "depends_on"
    summary: str
    severity: ImpactSeverity

@dataclass(frozen=True)
class Impact:
    affected_entities: tuple[AffectedEntity, ...]

    @classmethod
    def none(cls) -> "Impact":
        return cls(affected_entities=())

    @property
    def has_impact(self) -> bool:
        return len(self.affected_entities) > 0
```

**Tests:**
- Construction and immutability
- `none()` factory
- `has_impact` property

### 1.3 RemediationAction Model

**File:** `src/new_wazi/domain/model/remediation_action.py` (NEW)

```python
class ActionType(Enum):
    REWRITE_PLAN = "REWRITE_PLAN"
    APPLY_CROSSWALK = "APPLY_CROSSWALK"
    ACK_ONLY = "ACK_ONLY"
    UPDATE_CATALOG = "UPDATE_CATALOG"
    DEFINE_INDICATOR = "DEFINE_INDICATOR"

@dataclass(frozen=True)
class RemediationAction:
    action_type: ActionType
    description: str
    parameters: dict = field(default_factory=dict)

    def __post_init__(self):
        # Freeze parameters dict
        object.__setattr__(self, 'parameters', MappingProxyType(self.parameters))
```

**Note:** This complements the existing `Remediation` class. `Remediation` is a suggestion; `RemediationAction` is a typed, executable action.

**Tests:**
- All action types
- Parameters immutability
- Description required

### 1.4 Extend Issue with Optional Fields

**File:** `src/new_wazi/domain/model/validation.py` (MODIFY)

```python
@dataclass(frozen=True)
class Issue:
    code: str
    severity: Severity
    message: str
    details: dict = field(default_factory=dict)
    remediations: tuple[Remediation, ...] = ()
    # NEW: Optional enrichments
    attributions: tuple[Attribution, ...] = ()
    impacts: tuple[Impact, ...] = ()
    remediation_actions: tuple[RemediationAction, ...] = ()
    context_links: tuple[str, ...] = ()  # doc refs

    def with_attribution(self, attribution: Attribution) -> "Issue":
        """Return new Issue with attribution added."""
        return Issue(
            code=self.code,
            severity=self.severity,
            message=self.message,
            details=self.details,
            remediations=self.remediations,
            attributions=self.attributions + (attribution,),
            impacts=self.impacts,
            remediation_actions=self.remediation_actions,
            context_links=self.context_links,
        )

    def with_impact(self, impact: Impact) -> "Issue":
        """Return new Issue with impact added."""
        ...
```

**Backwards Compatibility:** All new fields have defaults. Existing code continues to work.

**Tests:**
- Existing tests still pass
- New fields default to empty
- `with_attribution()` and `with_impact()` methods

### 1.5 RulesetPack Model

**File:** `src/new_wazi/domain/model/ruleset_pack.py` (NEW)

```python
@dataclass(frozen=True)
class RulesetPack:
    id: str
    version: str
    enabled_checks: tuple[str, ...]
    severity_overrides: dict[str, Severity] = field(default_factory=dict)
    allow_rewrites: bool = True
    require_ack_for: tuple[str, ...] = ()

    def is_enabled(self, check_code: str) -> bool:
        return check_code in self.enabled_checks

    def get_severity(self, check_code: str, default: Severity) -> Severity:
        return self.severity_overrides.get(check_code, default)

    def requires_ack(self, issue_code: str) -> bool:
        return issue_code in self.require_ack_for
```

**Built-in packs:**
```python
CORE_PACK = RulesetPack(
    id="core",
    version="1.0.0",
    enabled_checks=("GRAIN_VALIDATION", "MEASURE_TYPE", "INDICATOR_AGGREGATION"),
)

STANDARD_PACK = RulesetPack(
    id="standard",
    version="1.0.0",
    enabled_checks=("GRAIN_VALIDATION", "MEASURE_TYPE", "INDICATOR_AGGREGATION",
                    "COMPARABILITY", "SUPPRESSION"),
    require_ack_for=("PARTIAL_COMPARABILITY",),
)

REGULATED_PACK = RulesetPack(
    id="regulated",
    version="1.0.0",
    enabled_checks=("GRAIN_VALIDATION", "MEASURE_TYPE", "INDICATOR_AGGREGATION",
                    "COMPARABILITY", "SUPPRESSION", "FRESHNESS", "UNIVERSE_REQUIRED"),
    severity_overrides={
        "FRESHNESS_VIOLATED": Severity.BLOCK,
        "SUPPRESSION_VIOLATED": Severity.BLOCK,
    },
    require_ack_for=("GEO_VERSION_MISMATCH", "UNIVERSE_CONFLICT"),
)
```

**Tests:**
- `is_enabled()` for various checks
- `get_severity()` with and without override
- `requires_ack()` behavior

---

## Phase 2: Semantic Check Infrastructure

**Goal:** Create the SemanticCheck abstraction that produces rich CheckResults.

### 2.1 CheckResult Model

**File:** `src/new_wazi/domain/model/check_result.py` (NEW)

```python
@dataclass(frozen=True)
class CheckResult:
    passed: bool
    severity: Severity = Severity.ALLOW
    code: str = ""
    message: str = ""
    attributions: tuple[Attribution, ...] = ()
    impacts: tuple[Impact, ...] = ()
    remediation_actions: tuple[RemediationAction, ...] = ()
    disclosures: tuple[Disclosure, ...] = ()

    @classmethod
    def passed_result(cls) -> "CheckResult":
        return cls(passed=True)

    def to_issue(self, subject_id: str | None = None) -> Issue:
        """Convert to Issue for inclusion in ValidationResult."""
        details = {"subject_id": subject_id} if subject_id else {}
        return Issue(
            code=self.code,
            severity=self.severity,
            message=self.message,
            details=details,
            attributions=self.attributions,
            impacts=self.impacts,
            remediation_actions=self.remediation_actions,
        )
```

**Tests:**
- `passed_result()` factory
- `to_issue()` conversion
- All fields properly copied

### 2.2 SemanticCheck Protocol

**File:** `src/new_wazi/domain/services/semantic_check.py` (NEW)

```python
class SemanticCheck(Protocol):
    """Protocol for semantic checks that evaluate claims."""

    @property
    def code(self) -> str:
        """Unique check code for ruleset configuration."""
        ...

    def evaluate(
        self,
        plan: QueryPlan,
        catalog: CatalogSnapshot,
    ) -> CheckResult:
        """Evaluate the check and return structured result."""
        ...
```

### 2.3 Migrate Existing Rules to SemanticChecks

**File:** `src/new_wazi/domain/services/checks/indicator_aggregation.py` (NEW)

Migrate `IndicatorAggregationRule` to new structure:

```python
class IndicatorAggregationCheck:
    code = "INDICATOR_AGGREGATION"

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        # Same logic as current IndicatorAggregationRule
        # But return CheckResult with remediation_actions
        ...
```

**Additional checks to implement:**
- `GrainValidationCheck` - validate grain consistency
- `MeasureTypeCheck` - validate measure types
- `ComparabilityCheck` - check dataset comparability
- `UniverseRequiredCheck` - enforce universe presence
- `CrosswalkRequiredCheck` - enforce crosswalk for version mismatch

### 2.4 SemanticValidator Service

**File:** `src/new_wazi/domain/services/semantic_validator.py` (NEW)

```python
class SemanticValidator:
    def __init__(self, checks: tuple[SemanticCheck, ...], pack: RulesetPack):
        self._checks = checks
        self._pack = pack

    def validate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> ValidationResult:
        issues = []
        disclosures = []

        for check in self._checks:
            if not self._pack.is_enabled(check.code):
                continue

            result = check.evaluate(plan, catalog)
            if not result.passed:
                # Apply severity override from pack
                severity = self._pack.get_severity(check.code, result.severity)
                issue = result.to_issue().with_severity(severity)
                issues.append(issue)
                disclosures.extend(result.disclosures)

        return ValidationResult(
            query_id=plan.query_id,
            status=self._compute_status(issues),
            issues=tuple(issues),
            disclosures=tuple(disclosures),
        )
```

**Tests:**
- Respects `enabled_checks` from pack
- Applies `severity_overrides`
- Computes correct status

---

## Phase 3: Quality Rules (Freshness)

**Goal:** Implement freshness as a semantic guarantee, not a pipeline concern.

### 3.1 FreshnessGuarantee Value Object

**File:** `src/new_wazi/domain/model/quality.py` (NEW)

```python
@dataclass(frozen=True)
class FreshnessGuarantee:
    max_staleness_hours: int

    def __post_init__(self):
        if self.max_staleness_hours <= 0:
            raise ValueError("max_staleness_hours must be positive")

@dataclass(frozen=True)
class FreshnessMetadata:
    last_updated_at: datetime
    checked_at: datetime

    @property
    def staleness_hours(self) -> float:
        return (self.checked_at - self.last_updated_at).total_seconds() / 3600
```

### 3.2 Extend Dataset with Freshness

**File:** `src/new_wazi/domain/model/dataset.py` (MODIFY)

```python
@dataclass
class Dataset:
    # ... existing fields ...
    freshness_guarantee: FreshnessGuarantee | None = None
```

### 3.3 Extend CatalogStore Port

**File:** `src/new_wazi/application/ports/catalog_store.py` (MODIFY)

```python
class CatalogStore(Protocol):
    # ... existing methods ...

    def get_freshness_metadata(
        self,
        dataset_id: DatasetId,
    ) -> FreshnessMetadata | None:
        """Return freshness metadata if available."""
        ...
```

### 3.4 FreshnessCheck Implementation

**File:** `src/new_wazi/domain/services/checks/freshness.py` (NEW)

```python
class FreshnessCheck:
    code = "FRESHNESS"

    def __init__(self, catalog_store: CatalogStore):
        self._catalog = catalog_store

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        for dp_id in plan.get_data_product_ids():
            dp = catalog.get_data_product(dp_id)
            dataset = self._catalog.get_dataset(dp.dataset_id)

            if dataset.freshness_guarantee is None:
                continue

            meta = self._catalog.get_freshness_metadata(dataset.id)
            if meta is None:
                return CheckResult(
                    passed=False,
                    severity=Severity.WARN,
                    code="FRESHNESS_UNKNOWN",
                    message=f"Dataset claims freshness but no metadata available",
                    remediation_actions=(
                        RemediationAction(ActionType.ACK_ONLY, "Acknowledge unknown freshness"),
                    ),
                )

            if meta.staleness_hours > dataset.freshness_guarantee.max_staleness_hours:
                return CheckResult(
                    passed=False,
                    severity=Severity.REQUIRE_ACK,
                    code="FRESHNESS_VIOLATED",
                    message=f"Data stale: {meta.staleness_hours:.1f}h > {dataset.freshness_guarantee.max_staleness_hours}h",
                    disclosures=(
                        Disclosure("STALE_DATA", f"Last updated {meta.last_updated_at.isoformat()}"),
                    ),
                )

        return CheckResult.passed_result()
```

**Tests:**
- No guarantee = pass
- Within guarantee = pass
- Exceeded guarantee = REQUIRE_ACK
- No metadata = WARN

---

## Phase 4: Attribution Infrastructure

**Goal:** Enable dimensional diagnosis of issues via optional port.

### 4.1 AttributionProvider Port

**File:** `src/new_wazi/application/ports/attribution_provider.py` (NEW)

```python
@dataclass(frozen=True)
class AttributionRequest:
    issue_code: str
    dataset_id: DatasetId
    dimensions: tuple[AttributionDimension, ...]
    filter_context: dict

class AttributionProvider(Protocol):
    def compute_attribution(self, request: AttributionRequest) -> Attribution:
        ...

class NullAttributionProvider:
    """Default implementation: no attribution available."""

    def compute_attribution(self, request: AttributionRequest) -> Attribution:
        return Attribution.unavailable()
```

### 4.2 Fake Implementation for Testing

**File:** `tests/unit/application/fakes.py` (MODIFY)

```python
class FakeAttributionProvider:
    def __init__(self):
        self._attributions: dict[str, Attribution] = {}

    def set_attribution(self, issue_code: str, attribution: Attribution) -> None:
        self._attributions[issue_code] = attribution

    def compute_attribution(self, request: AttributionRequest) -> Attribution:
        return self._attributions.get(request.issue_code, Attribution.unavailable())
```

### 4.3 EnrichWithAttribution Use Case

**File:** `src/new_wazi/application/use_cases/enrich_with_attribution.py` (NEW)

```python
ATTRIBUTABLE_ISSUES = frozenset({
    "SUPPRESSION_TRIGGERED",
    "SMALL_CELL_WARNING",
    "AGGREGATION_MISMATCH",
    "UNIVERSE_CONFLICT",
})

class EnrichWithAttributionUseCase:
    def __init__(
        self,
        attribution_provider: AttributionProvider,
        catalog_store: CatalogStore,
    ):
        self._provider = attribution_provider
        self._catalog = catalog_store

    def execute(
        self,
        issues: tuple[Issue, ...],
        plan: QueryPlan,
        catalog: CatalogSnapshot,
    ) -> tuple[Issue, ...]:
        enriched = []
        for issue in issues:
            if issue.code not in ATTRIBUTABLE_ISSUES:
                enriched.append(issue)
                continue

            dimensions = self._get_dimensions(issue, catalog)
            request = AttributionRequest(
                issue_code=issue.code,
                dataset_id=self._get_dataset_id(issue),
                dimensions=dimensions,
                filter_context=plan.get_filter_context(),
            )

            attribution = self._provider.compute_attribution(request)
            enriched.append(issue.with_attribution(attribution))

        return tuple(enriched)
```

**Tests:**
- Non-attributable issues unchanged
- Attributable issues get attribution attached
- NullProvider returns unavailable

---

## Phase 5: Impact Analysis

**Goal:** Enable meaning-level dependency traversal.

### 5.1 SemanticImpactAnalyzer Service

**File:** `src/new_wazi/application/services/semantic_impact_analyzer.py` (NEW)

```python
class SemanticImpactAnalyzer:
    def __init__(self, catalog_store: CatalogStore):
        self._catalog = catalog_store

    def analyze(self, entity_type: str, entity_id: str) -> Impact:
        if entity_type == "DATASET":
            return self._analyze_dataset(DatasetId.from_string(entity_id))
        elif entity_type == "INDICATOR":
            return self._analyze_indicator(VariableId.from_string(entity_id))
        elif entity_type == "GEOGRAPHY_VERSION":
            return self._analyze_geo_version(ReferenceSystemVersionId.from_string(entity_id))
        elif entity_type == "UNIVERSE":
            return self._analyze_universe(UniverseId.from_string(entity_id))
        else:
            return Impact.none()

    def _analyze_dataset(self, dataset_id: DatasetId) -> Impact:
        affected = []

        # Find data products using this dataset
        for dp in self._catalog.list_data_products(dataset_id=dataset_id):
            affected.append(AffectedEntity(
                entity_type="DATA_PRODUCT",
                entity_id=str(dp.id),
                relation="belongs_to",
                summary=f"Data product '{dp.name}' depends on this dataset",
                severity=ImpactSeverity.HIGH,
            ))

            # Find indicators in this data product
            for var in dp.variables:
                if var.role == VariableRole.INDICATOR:
                    defn = self._catalog.get_indicator_definition(var.id)
                    if defn:
                        affected.append(AffectedEntity(
                            entity_type="INDICATOR",
                            entity_id=str(var.id),
                            relation="defined_in",
                            summary=f"Indicator '{var.name}' would be affected",
                            severity=ImpactSeverity.HIGH,
                        ))

        return Impact(affected_entities=tuple(affected))

    def _analyze_indicator(self, indicator_id: VariableId) -> Impact:
        # Find what uses this indicator as numerator/denominator
        ...

    def _analyze_geo_version(self, version_id: ReferenceSystemVersionId) -> Impact:
        # Find datasets using this version
        ...

    def _analyze_universe(self, universe_id: UniverseId) -> Impact:
        # Find datasets with this universe
        ...
```

### 5.2 AnalyzeSemanticImpact Use Case

**File:** `src/new_wazi/application/use_cases/analyze_semantic_impact.py` (NEW)

```python
@dataclass(frozen=True)
class ImpactReportDTO:
    entity_type: str
    entity_id: str
    affected_count: int
    affected_entities: tuple[dict, ...]
    high_severity_count: int

class AnalyzeSemanticImpactUseCase:
    def __init__(self, impact_analyzer: SemanticImpactAnalyzer):
        self._analyzer = impact_analyzer

    def execute(self, entity_type: str, entity_id: str) -> ImpactReportDTO:
        impact = self._analyzer.analyze(entity_type, entity_id)

        return ImpactReportDTO(
            entity_type=entity_type,
            entity_id=entity_id,
            affected_count=len(impact.affected_entities),
            affected_entities=tuple(
                {
                    "entity_type": ae.entity_type,
                    "entity_id": ae.entity_id,
                    "relation": ae.relation,
                    "summary": ae.summary,
                    "severity": ae.severity.value,
                }
                for ae in impact.affected_entities
            ),
            high_severity_count=sum(
                1 for ae in impact.affected_entities
                if ae.severity in (ImpactSeverity.HIGH, ImpactSeverity.CRITICAL)
            ),
        )
```

**Tests:**
- Dataset impact finds data products and indicators
- Indicator impact finds dependents
- Empty impact for unknown entity

---

## Phase 6: Context Slices & Tool Contracts

**Goal:** Enable LLM-safe projections and tool discovery.

### 6.1 ContextSliceProjector Service

**File:** `src/new_wazi/application/services/context_slice_projector.py` (NEW)

```python
class ContextSliceProjector:
    @staticmethod
    def validation_summary(result: ValidationResult, max_issues: int = 10) -> dict:
        return {
            "valid": result.is_allowed,
            "issue_count": len(result.issues),
            "blocking_issues": [
                {"code": i.code, "message": i.message}
                for i in result.issues
                if i.severity == Severity.BLOCK
            ][:max_issues],
            "required_acknowledgments": [
                {"code": i.code, "message": i.message}
                for i in result.issues
                if i.severity == Severity.REQUIRE_ACK
            ][:max_issues],
            "disclosures": [d.text for d in result.disclosures],
        }

    @staticmethod
    def indicator_explanation(
        indicator: Variable,
        definition: IndicatorDefinition | None,
    ) -> dict:
        return {
            "id": str(indicator.id),
            "name": indicator.name,
            "description": indicator.description,
            "aggregation_rule": definition.aggregation_policy.value if definition else "UNKNOWN",
            "can_average": definition.can_aggregate_with(AggregationType.AVG) if definition else False,
            "numerator": str(definition.numerator_ref.variable_id) if definition and definition.numerator_ref else None,
            "denominator": str(definition.denominator_ref.variable_id) if definition and definition.denominator_ref else None,
            "formula": definition.formula if definition else None,
        }

    @staticmethod
    def comparability_report(report: ComparabilityReport) -> dict:
        return {
            "source_id": str(report.source_dataset_id),
            "target_id": str(report.target_dataset_id),
            "level": report.overall_level.value,
            "compatible": report.overall_level != ComparabilityLevel.NONE,
            "issues": [
                {"reason": c.reasons[0].value if c.reasons else "UNKNOWN", "level": c.level.value}
                for c in report.checks
                if c.level != ComparabilityLevel.FULL
            ],
        }

    @staticmethod
    def dataset_summary(dataset: Dataset) -> dict:
        return {
            "id": str(dataset.id),
            "name": dataset.name,
            "description": dataset.description,
            "collection_period": f"{dataset.collection_start} to {dataset.collection_end}" if dataset.collection_start else None,
            "reference_date": str(dataset.reference_date) if dataset.reference_date else None,
            "has_freshness_guarantee": dataset.freshness_guarantee is not None,
        }
```

### 6.2 ToolContract Model

**File:** `src/new_wazi/domain/model/tool_contract.py` (NEW)

```python
@dataclass(frozen=True)
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    enum_values: tuple[str, ...] | None = None

@dataclass(frozen=True)
class ToolContract:
    name: str
    description: str
    parameters: tuple[ToolParameter, ...]
    returns: str
    examples: tuple[dict, ...] = ()
```

### 6.3 ToolRegistry Service

**File:** `src/new_wazi/application/services/tool_registry.py` (NEW)

```python
class ToolRegistry:
    _contracts: dict[str, ToolContract] = {}

    @classmethod
    def register(cls, contract: ToolContract) -> None:
        cls._contracts[contract.name] = contract

    @classmethod
    def get_contracts(cls) -> tuple[ToolContract, ...]:
        return tuple(cls._contracts.values())

    @classmethod
    def get_contract(cls, name: str) -> ToolContract | None:
        return cls._contracts.get(name)

# Register built-in tools
ToolRegistry.register(ToolContract(
    name="validate_query",
    description="Validate a query plan against catalog semantics",
    parameters=(
        ToolParameter("plan", "query_plan", "The query plan to validate"),
        ToolParameter("ruleset", "string", "Ruleset pack to use", required=False,
                      enum_values=("core", "standard", "regulated")),
    ),
    returns="ValidationResult with issues, disclosures, and remediations",
))

ToolRegistry.register(ToolContract(
    name="analyze_impact",
    description="Analyze semantic impact of changing a catalog entity",
    parameters=(
        ToolParameter("entity_type", "string", "Type of entity",
                      enum_values=("dataset", "indicator", "geography_version", "universe")),
        ToolParameter("entity_id", "string", "ID of the entity"),
    ),
    returns="ImpactReport with affected entities and severity",
))

ToolRegistry.register(ToolContract(
    name="explain_indicator",
    description="Get explanation of an indicator's semantics",
    parameters=(
        ToolParameter("indicator_id", "string", "ID of the indicator"),
    ),
    returns="Indicator explanation with definition and aggregation rules",
))

ToolRegistry.register(ToolContract(
    name="check_comparability",
    description="Check if two datasets can be compared",
    parameters=(
        ToolParameter("source_id", "string", "First dataset ID"),
        ToolParameter("target_id", "string", "Second dataset ID"),
    ),
    returns="ComparabilityResult with level and reasons",
))
```

### 6.4 ExecuteTool Use Case

**File:** `src/new_wazi/application/use_cases/execute_tool.py` (NEW)

```python
@dataclass(frozen=True)
class ToolResult:
    success: bool
    data: dict | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: dict) -> "ToolResult":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        return cls(success=False, error=error)

class ExecuteToolUseCase:
    def __init__(
        self,
        validate_query: ValidateQueryUseCase,
        analyze_impact: AnalyzeSemanticImpactUseCase,
        comparability_resolver: ComparabilityResolver,
        catalog_store: CatalogStore,
        context_projector: ContextSliceProjector,
    ):
        self._tools = {
            "validate_query": self._execute_validate,
            "analyze_impact": self._execute_impact,
            "explain_indicator": self._execute_explain,
            "check_comparability": self._execute_comparability,
        }
        self._validate = validate_query
        self._impact = analyze_impact
        self._comparability = comparability_resolver
        self._catalog = catalog_store
        self._projector = context_projector

    def execute(self, tool_name: str, params: dict) -> ToolResult:
        if tool_name not in self._tools:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        contract = ToolRegistry.get_contract(tool_name)
        if contract:
            validation_error = self._validate_params(params, contract)
            if validation_error:
                return ToolResult.fail(validation_error)

        try:
            return self._tools[tool_name](params)
        except Exception as e:
            return ToolResult.fail(str(e))

    def _execute_validate(self, params: dict) -> ToolResult:
        # Build and validate query, return projected result
        ...

    def _execute_impact(self, params: dict) -> ToolResult:
        report = self._impact.execute(params["entity_type"], params["entity_id"])
        return ToolResult.ok(asdict(report))

    def _execute_explain(self, params: dict) -> ToolResult:
        # Get indicator and definition, project explanation
        ...

    def _execute_comparability(self, params: dict) -> ToolResult:
        # Run comparability check, project result
        ...
```

**Tests:**
- Unknown tool returns error
- Missing required params returns error
- Each tool returns projected result
- Errors are caught and returned as ToolResult.fail

---

## Phase 7: Integration & Wiring

**Goal:** Wire everything together in the validation pipeline.

### 7.1 ValidatorFactory

**File:** `src/new_wazi/domain/services/validator_factory.py` (NEW)

```python
class ValidatorFactory:
    _packs = {
        "core": CORE_PACK,
        "standard": STANDARD_PACK,
        "regulated": REGULATED_PACK,
    }

    @classmethod
    def create(cls, pack_id: str, catalog_store: CatalogStore) -> SemanticValidator:
        pack = cls._packs.get(pack_id, STANDARD_PACK)

        checks = (
            IndicatorAggregationCheck(),
            GrainValidationCheck(),
            MeasureTypeCheck(),
            ComparabilityCheck(),
            FreshnessCheck(catalog_store),
            UniverseRequiredCheck(),
            CrosswalkRequiredCheck(),
        )

        return SemanticValidator(checks, pack)

    @classmethod
    def register_pack(cls, pack: RulesetPack) -> None:
        cls._packs[pack.id] = pack
```

### 7.2 Update ValidateQueryUseCase

**File:** `src/new_wazi/application/use_cases/validate_query.py` (MODIFY)

```python
class ValidateQueryUseCase:
    def __init__(
        self,
        catalog_store: CatalogStore,
        id_generator: IdGenerator,
        pack_id: str = "standard",
        attribution_provider: AttributionProvider | None = None,
    ):
        self._catalog = catalog_store
        self._id_gen = id_generator
        self._validator = ValidatorFactory.create(pack_id, catalog_store)
        self._attribution = attribution_provider or NullAttributionProvider()
        self._enricher = EnrichWithAttributionUseCase(self._attribution, catalog_store)

    def execute(self, request: QueryRequest) -> ValidationResultDTO:
        # ... existing plan building ...

        result = self._validator.validate(plan, snapshot)

        # Enrich with attributions
        enriched_issues = self._enricher.execute(result.issues, plan, snapshot)

        result = ValidationResult(
            query_id=result.query_id,
            status=result.status,
            issues=enriched_issues,
            disclosures=result.disclosures,
        )

        return self._to_dto(result)
```

---

## Phase 8: DTO Extensions

**Goal:** Update DTOs to carry new fields.

### 8.1 Extended ValidationResultDTO

**File:** `src/new_wazi/application/dto/validation_dto.py` (MODIFY)

```python
@dataclass(frozen=True)
class AttributionSliceDTO:
    dimension_name: str
    value: str
    contribution_score: float
    row_count: int | None
    note: str | None

@dataclass(frozen=True)
class AttributionDTO:
    slices: tuple[AttributionSliceDTO, ...]
    method: str

@dataclass(frozen=True)
class ImpactDTO:
    entity_type: str
    entity_id: str
    relation: str
    summary: str
    severity: str

@dataclass(frozen=True)
class RemediationActionDTO:
    action_type: str
    description: str
    parameters: dict

@dataclass(frozen=True)
class IssueDTO:
    code: str
    severity: str
    message: str
    details: dict
    remediations: tuple[RemediationDTO, ...]
    # NEW fields
    attributions: tuple[AttributionDTO, ...] = ()
    impacts: tuple[ImpactDTO, ...] = ()
    remediation_actions: tuple[RemediationActionDTO, ...] = ()
    context_links: tuple[str, ...] = ()
```

---

## Implementation Order

### Milestone 1: Foundation (Week 1)
1. Phase 1.1-1.3: Attribution, Impact, RemediationAction models
2. Phase 1.4: Extend Issue with new fields
3. Phase 1.5: RulesetPack model
4. Unit tests for all new models

### Milestone 2: Check Infrastructure (Week 2)
1. Phase 2.1-2.2: CheckResult and SemanticCheck protocol
2. Phase 2.3: Migrate IndicatorAggregationRule
3. Phase 2.4: SemanticValidator service
4. Unit tests for check infrastructure

### Milestone 3: Quality Rules (Week 3)
1. Phase 3.1-3.2: FreshnessGuarantee, extend Dataset
2. Phase 3.3: Extend CatalogStore
3. Phase 3.4: FreshnessCheck implementation
4. Unit tests and fake updates

### Milestone 4: Attribution & Impact (Week 4)
1. Phase 4: AttributionProvider port and use case
2. Phase 5: SemanticImpactAnalyzer and use case
3. Unit tests with fakes

### Milestone 5: AI Integration (Week 5)
1. Phase 6.1-6.2: ContextSliceProjector and ToolContract
2. Phase 6.3-6.4: ToolRegistry and ExecuteTool
3. Unit tests for tool execution

### Milestone 6: Integration (Week 6)
1. Phase 7: ValidatorFactory and pipeline wiring
2. Phase 8: DTO extensions
3. Integration tests
4. Documentation updates

---

## Testing Strategy

### Unit Tests
- Each new model in isolation
- Each check in isolation with mock catalog
- Each use case with fakes
- ContextSliceProjector output validation

### Integration Tests
- Full validation pipeline with semantic checks
- Tool execution end-to-end
- Impact analysis with real catalog graph

### Regression Tests
- Existing validation tests continue to pass
- Existing use case tests unchanged

---

## Migration Notes

### Backwards Compatibility
- All new Issue fields have defaults
- Existing Rule protocol still works
- SemanticCheck is additive
- RulesetPack is optional (defaults to "standard")

### Deprecation Path
1. Keep existing `Rule` protocol working
2. Migrate rules to `SemanticCheck` one at a time
3. Eventually deprecate `Rule` in favor of `SemanticCheck`

---

## Files to Create

```
src/new_wazi/domain/model/
  attribution.py          (NEW)
  impact.py               (NEW)
  remediation_action.py   (NEW)
  check_result.py         (NEW)
  ruleset_pack.py         (NEW)
  tool_contract.py        (NEW)
  quality.py              (NEW)

src/new_wazi/domain/services/
  semantic_check.py       (NEW)
  semantic_validator.py   (NEW)
  validator_factory.py    (NEW)
  checks/
    __init__.py           (NEW)
    indicator_aggregation.py  (NEW - migrated)
    grain_validation.py   (NEW)
    measure_type.py       (NEW)
    comparability.py      (NEW)
    freshness.py          (NEW)
    universe_required.py  (NEW)
    crosswalk_required.py (NEW)

src/new_wazi/application/ports/
  attribution_provider.py (NEW)

src/new_wazi/application/services/
  semantic_impact_analyzer.py   (NEW)
  context_slice_projector.py    (NEW)
  tool_registry.py              (NEW)

src/new_wazi/application/use_cases/
  analyze_semantic_impact.py    (NEW)
  enrich_with_attribution.py    (NEW)
  execute_tool.py               (NEW)

src/new_wazi/application/dto/
  context_slices.py             (NEW)
```

## Files to Modify

```
src/new_wazi/domain/model/
  validation.py           (extend Issue)
  dataset.py              (add freshness_guarantee)

src/new_wazi/application/ports/
  catalog_store.py        (add get_freshness_metadata)

src/new_wazi/application/use_cases/
  validate_query.py       (wire SemanticValidator)

src/new_wazi/application/dto/
  validation_dto.py       (extend IssueDTO)

tests/unit/application/
  fakes.py                (add FakeAttributionProvider, update FakeCatalogStore)
```
