"""Tests for Concept and Universe entities in Identity component.

These tests verify:
1. Concept can be imported from invariant.identity
2. Universe can be imported from invariant.identity
3. Both still work from old location (backward compatibility)
4. ConceptVersion has effective_from field
"""

from datetime import date


def test_concept_importable_from_identity():
    """Concept can be imported from identity component."""
    from invariant.identity import Concept

    assert Concept is not None


def test_universe_importable_from_identity():
    """Universe can be imported from identity component."""
    from invariant.identity import Universe

    assert Universe is not None


def test_concept_backward_compatible():
    """Concept still importable from old location."""
    from invariant.identity.domain.entities import Concept

    assert Concept is not None


def test_universe_backward_compatible():
    """Universe still importable from old location."""
    from invariant.identity.domain.entities import Universe

    assert Universe is not None


def test_concept_version_has_effective_from():
    """ConceptVersion has effective_from field."""
    from invariant.identity import ConceptVersion

    assert hasattr(ConceptVersion, "__dataclass_fields__")
    assert "effective_from" in ConceptVersion.__dataclass_fields__


def test_concept_creation():
    """Concept can be instantiated with required fields."""
    from invariant.identity import Concept
    from invariant.shared.contracts.ids import ConceptId

    concept_id = ConceptId.create()
    concept = Concept(
        id=concept_id,
        label="Population Count",
        description="Total number of people in an area",
    )

    assert concept.id == concept_id
    assert concept.label == "Population Count"
    assert concept.description == "Total number of people in an area"
    assert concept.canonical_unit is None


def test_concept_with_canonical_unit():
    """Concept can be created with canonical_unit."""
    from invariant.identity import Concept
    from invariant.shared.contracts.ids import ConceptId

    concept_id = ConceptId.create()
    concept = Concept(
        id=concept_id,
        label="Temperature",
        description="Measured temperature",
        canonical_unit="celsius",
    )

    assert concept.canonical_unit == "celsius"


def test_universe_creation():
    """Universe can be instantiated with required fields."""
    from invariant.identity import Universe
    from invariant.shared.contracts.ids import UniverseId

    universe_id = UniverseId.create()
    universe = Universe(
        id=universe_id,
        label="South African Population",
        definition="All persons residing in South Africa",
    )

    assert universe.id == universe_id
    assert universe.label == "South African Population"
    assert universe.definition == "All persons residing in South Africa"
    assert universe.inclusions == ()
    assert universe.exclusions == ()


def test_universe_with_inclusions():
    """Universe can be created with inclusions only."""
    from invariant.identity import Universe
    from invariant.shared.contracts.ids import UniverseId

    universe_id = UniverseId.create()
    universe = Universe(
        id=universe_id,
        label="Working Age Adults",
        definition="Adults of working age in South Africa",
        inclusions=["Citizens", "Permanent residents"],
    )

    assert universe.inclusions == ("Citizens", "Permanent residents")
    assert universe.exclusions == ()


def test_universe_with_exclusions():
    """Universe can be created with exclusions only."""
    from invariant.identity import Universe
    from invariant.shared.contracts.ids import UniverseId

    universe_id = UniverseId.create()
    universe = Universe(
        id=universe_id,
        label="Working Age Adults",
        definition="Adults of working age in South Africa",
        exclusions=["Children under 15", "Elderly over 65"],
    )

    assert universe.inclusions == ()
    assert universe.exclusions == ("Children under 15", "Elderly over 65")


def test_concept_version_creation():
    """ConceptVersion can be instantiated with effective_from."""
    from invariant.identity import ConceptVersion
    from invariant.shared.contracts.ids import ConceptId

    concept_id = ConceptId.create()
    version = ConceptVersion(
        concept_id=concept_id,
        version=1,
        effective_from=date(2024, 1, 1),
        label="Population Count",
        description="Total number of people in an area",
    )

    assert version.concept_id == concept_id
    assert version.version == 1
    assert version.effective_from == date(2024, 1, 1)
    assert version.label == "Population Count"


def test_concept_version_is_frozen():
    """ConceptVersion is immutable."""
    from datetime import date

    from invariant.identity import ConceptVersion
    from invariant.shared.contracts.ids import ConceptId

    concept_id = ConceptId.create()
    version = ConceptVersion(
        concept_id=concept_id,
        version=1,
        effective_from=date(2024, 1, 1),
        label="Population Count",
        description="Total number of people in an area",
    )

    # Attempting to modify should raise FrozenInstanceError
    from dataclasses import FrozenInstanceError

    import pytest

    with pytest.raises(FrozenInstanceError):
        version.label = "New Label"


def test_identity_same_as_semantic_concept():
    """Concept from identity is the same class as semantic.Concept."""
    from invariant.identity import Concept as IdentityConcept
    from invariant.identity.domain.entities import Concept as SemanticConcept

    assert IdentityConcept is SemanticConcept


def test_identity_same_as_semantic_universe():
    """Universe from identity is the same class as semantic.Universe."""
    from invariant.identity import Universe as IdentityUniverse
    from invariant.identity.domain.entities import Universe as SemanticUniverse

    assert IdentityUniverse is SemanticUniverse


# --- Invariant validation tests ---


def test_universe_rejects_both_inclusions_and_exclusions():
    """Universe cannot have both inclusions and exclusions."""
    import pytest

    from invariant.identity import Universe
    from invariant.shared.contracts.ids import UniverseId

    universe_id = UniverseId.create()

    with pytest.raises(ValueError, match="cannot have both inclusions and exclusions"):
        Universe(
            id=universe_id,
            label="Invalid Universe",
            definition="This should fail",
            inclusions=["Citizens"],
            exclusions=["Non-citizens"],
        )


def test_concept_rejects_empty_label():
    """Concept must have a non-empty label."""
    import pytest

    from invariant.identity import Concept
    from invariant.shared.contracts.ids import ConceptId

    concept_id = ConceptId.create()

    with pytest.raises(ValueError, match="label cannot be empty"):
        Concept(
            id=concept_id,
            label="",
            description="Some description",
        )


def test_concept_rejects_whitespace_only_label():
    """Concept label cannot be whitespace only."""
    import pytest

    from invariant.identity import Concept
    from invariant.shared.contracts.ids import ConceptId

    concept_id = ConceptId.create()

    with pytest.raises(ValueError, match="label cannot be empty"):
        Concept(
            id=concept_id,
            label="   ",
            description="Some description",
        )


def test_id_generator_protocol_importable():
    """IdGenerator protocol can be imported from ports."""
    from invariant.identity.application.ports import IdGenerator

    assert IdGenerator is not None


def test_id_generator_fake_implementation():
    """IdGenerator can be implemented with fake for testing."""
    from dataclasses import dataclass, field
    from typing import TYPE_CHECKING
    from uuid import UUID

    if TYPE_CHECKING:
        from invariant.identity.application.ports import IdGenerator

    @dataclass
    class FakeIdGenerator:
        """Fake implementation that returns predictable UUIDs."""

        _counter: int = field(default=0)

        def generate(self) -> UUID:
            self._counter += 1
            return UUID(int=self._counter)

    # Verify it conforms to protocol
    generator: IdGenerator = FakeIdGenerator()
    first_id = generator.generate()
    second_id = generator.generate()

    assert first_id == UUID(int=1)
    assert second_id == UUID(int=2)
    assert first_id != second_id
