"""Tests for GeoHierarchy domain entity and value objects."""

import pytest

from invariant.domain.model.geo_hierarchy import (
    GeoHierarchy,
    ParentRelationship,
    RollupOverride,
    RollupRules,
)
from invariant.domain.model.ids import GeoHierarchyId


class TestRollupOverride:
    def test_create_valid(self) -> None:
        override = RollupOverride(from_level="ward", to_level="province", allowed=False)
        assert override.from_level == "ward"
        assert override.to_level == "province"
        assert override.allowed is False

    def test_create_allowed_true(self) -> None:
        override = RollupOverride(
            from_level="municipality", to_level="province", allowed=True
        )
        assert override.allowed is True

    def test_empty_from_level_raises(self) -> None:
        with pytest.raises(ValueError, match="from_level must not be empty"):
            RollupOverride(from_level="", to_level="province", allowed=False)

    def test_empty_to_level_raises(self) -> None:
        with pytest.raises(ValueError, match="to_level must not be empty"):
            RollupOverride(from_level="ward", to_level="", allowed=False)

    def test_is_frozen(self) -> None:
        override = RollupOverride(from_level="ward", to_level="province", allowed=False)
        with pytest.raises(AttributeError):
            override.from_level = "other"  # type: ignore[misc]


class TestRollupRules:
    def test_create_default(self) -> None:
        rules = RollupRules()
        assert rules.default_allowed is True
        assert rules.overrides == ()

    def test_create_with_default_false(self) -> None:
        rules = RollupRules(default_allowed=False)
        assert rules.default_allowed is False

    def test_create_with_overrides(self) -> None:
        overrides = [
            RollupOverride(from_level="ward", to_level="province", allowed=False),
            RollupOverride(from_level="municipality", to_level="country", allowed=True),
        ]
        rules = RollupRules(default_allowed=True, overrides=overrides)
        assert len(rules.overrides) == 2
        assert rules.overrides[0].from_level == "ward"
        assert rules.overrides[1].allowed is True

    def test_is_frozen(self) -> None:
        rules = RollupRules()
        with pytest.raises(AttributeError):
            rules.default_allowed = False  # type: ignore[misc]


class TestParentRelationship:
    def test_create_valid(self) -> None:
        rel = ParentRelationship(parent_level="province")
        assert rel.parent_level == "province"
        assert rel.lookup_column is None

    def test_create_with_lookup_column(self) -> None:
        rel = ParentRelationship(parent_level="province", lookup_column="parent_code")
        assert rel.parent_level == "province"
        assert rel.lookup_column == "parent_code"

    def test_empty_parent_level_raises(self) -> None:
        with pytest.raises(ValueError, match="parent_level must not be empty"):
            ParentRelationship(parent_level="")

    def test_is_frozen(self) -> None:
        rel = ParentRelationship(parent_level="province")
        with pytest.raises(AttributeError):
            rel.parent_level = "other"  # type: ignore[misc]


class TestGeoHierarchy:
    def test_create_minimal(self) -> None:
        hierarchy = GeoHierarchy(
            id=GeoHierarchyId.create(),
            name="south_africa",
            levels=("country", "province", "municipality", "ward"),
        )
        assert hierarchy.name == "south_africa"
        assert hierarchy.levels == ("country", "province", "municipality", "ward")
        assert hierarchy.parent_relationships == {}
        assert hierarchy.rollup_rules.default_allowed is True

    def test_create_factory_method(self) -> None:
        hierarchy = GeoHierarchy.create(
            name="south_africa",
            levels=["country", "province", "municipality", "ward"],
        )
        assert isinstance(hierarchy.id, GeoHierarchyId)
        assert hierarchy.name == "south_africa"
        assert hierarchy.levels == ("country", "province", "municipality", "ward")

    def test_create_with_parent_relationships(self) -> None:
        hierarchy = GeoHierarchy.create(
            name="south_africa",
            levels=["country", "province", "municipality", "ward"],
            parent_relationships={
                "province": ParentRelationship("country"),
                "municipality": ParentRelationship("province"),
                "ward": ParentRelationship("municipality"),
            },
        )
        assert hierarchy.get_parent_level("province") == "country"
        assert hierarchy.get_parent_level("ward") == "municipality"

    def test_create_with_rollup_rules(self) -> None:
        rules = RollupRules(
            default_allowed=True,
            overrides=[
                RollupOverride(from_level="ward", to_level="country", allowed=False),
            ],
        )
        hierarchy = GeoHierarchy.create(
            name="south_africa",
            levels=["country", "province", "municipality", "ward"],
            rollup_rules=rules,
        )
        assert hierarchy.rollup_rules.default_allowed is True
        assert len(hierarchy.rollup_rules.overrides) == 1

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            GeoHierarchy(
                id=GeoHierarchyId.create(),
                name="",
                levels=("country",),
            )

    def test_empty_levels_raises(self) -> None:
        with pytest.raises(ValueError, match="levels must not be empty"):
            GeoHierarchy(
                id=GeoHierarchyId.create(),
                name="south_africa",
                levels=(),
            )

    def test_parent_relationship_key_not_in_levels_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"parent_relationships key 'district' not found in levels",
        ):
            GeoHierarchy(
                id=GeoHierarchyId.create(),
                name="south_africa",
                levels=("country", "province"),
                parent_relationships={
                    "district": ParentRelationship("province"),
                },
            )

    def test_parent_level_not_in_levels_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"parent_level 'region' for 'province' not found in levels",
        ):
            GeoHierarchy(
                id=GeoHierarchyId.create(),
                name="south_africa",
                levels=("country", "province"),
                parent_relationships={
                    "province": ParentRelationship("region"),
                },
            )


class TestGeoHierarchyCanRollup:
    @pytest.fixture
    def hierarchy_with_overrides(self) -> GeoHierarchy:
        """Create a hierarchy with specific rollup rules."""
        return GeoHierarchy.create(
            name="south_africa",
            levels=["country", "province", "municipality", "ward"],
            rollup_rules=RollupRules(
                default_allowed=True,
                overrides=[
                    RollupOverride(
                        from_level="ward", to_level="country", allowed=False
                    ),
                ],
            ),
        )

    @pytest.fixture
    def hierarchy_default_forbidden(self) -> GeoHierarchy:
        """Create a hierarchy with default rollup forbidden."""
        return GeoHierarchy.create(
            name="south_africa",
            levels=["country", "province", "municipality"],
            rollup_rules=RollupRules(
                default_allowed=False,
                overrides=[
                    RollupOverride(
                        from_level="municipality", to_level="province", allowed=True
                    ),
                ],
            ),
        )

    def test_can_rollup_same_level_always_allowed(
        self, hierarchy_with_overrides: GeoHierarchy
    ) -> None:
        assert hierarchy_with_overrides.can_rollup("ward", "ward") is True
        assert hierarchy_with_overrides.can_rollup("country", "country") is True

    def test_can_rollup_default_allowed(
        self, hierarchy_with_overrides: GeoHierarchy
    ) -> None:
        assert hierarchy_with_overrides.can_rollup("ward", "municipality") is True
        assert hierarchy_with_overrides.can_rollup("municipality", "province") is True

    def test_can_rollup_override_forbids(
        self, hierarchy_with_overrides: GeoHierarchy
    ) -> None:
        assert hierarchy_with_overrides.can_rollup("ward", "country") is False

    def test_can_rollup_default_forbidden(
        self, hierarchy_default_forbidden: GeoHierarchy
    ) -> None:
        assert (
            hierarchy_default_forbidden.can_rollup("municipality", "country") is False
        )

    def test_can_rollup_override_allows(
        self, hierarchy_default_forbidden: GeoHierarchy
    ) -> None:
        assert (
            hierarchy_default_forbidden.can_rollup("municipality", "province") is True
        )

    def test_can_rollup_invalid_from_level_raises(
        self, hierarchy_with_overrides: GeoHierarchy
    ) -> None:
        with pytest.raises(
            ValueError, match=r"from_level 'district' not found in hierarchy"
        ):
            hierarchy_with_overrides.can_rollup("district", "province")

    def test_can_rollup_invalid_to_level_raises(
        self, hierarchy_with_overrides: GeoHierarchy
    ) -> None:
        with pytest.raises(
            ValueError, match=r"to_level 'region' not found in hierarchy"
        ):
            hierarchy_with_overrides.can_rollup("ward", "region")


class TestGeoHierarchyLevelNavigation:
    @pytest.fixture
    def hierarchy(self) -> GeoHierarchy:
        """Create a standard hierarchy for testing."""
        return GeoHierarchy.create(
            name="south_africa",
            levels=["country", "province", "municipality", "ward"],
            parent_relationships={
                "province": ParentRelationship("country"),
                "municipality": ParentRelationship("province", "parent_prov_code"),
                "ward": ParentRelationship("municipality"),
            },
        )

    def test_get_level_index(self, hierarchy: GeoHierarchy) -> None:
        assert hierarchy.get_level_index("country") == 0
        assert hierarchy.get_level_index("province") == 1
        assert hierarchy.get_level_index("municipality") == 2
        assert hierarchy.get_level_index("ward") == 3

    def test_get_level_index_invalid_level_raises(
        self, hierarchy: GeoHierarchy
    ) -> None:
        with pytest.raises(
            ValueError, match=r"level 'district' not found in hierarchy"
        ):
            hierarchy.get_level_index("district")

    def test_is_ancestor_true(self, hierarchy: GeoHierarchy) -> None:
        assert hierarchy.is_ancestor("country", "ward") is True
        assert hierarchy.is_ancestor("province", "municipality") is True

    def test_is_ancestor_false_same_level(self, hierarchy: GeoHierarchy) -> None:
        assert hierarchy.is_ancestor("province", "province") is False

    def test_is_ancestor_false_descendant(self, hierarchy: GeoHierarchy) -> None:
        assert hierarchy.is_ancestor("ward", "country") is False

    def test_get_parent_level_exists(self, hierarchy: GeoHierarchy) -> None:
        assert hierarchy.get_parent_level("ward") == "municipality"
        assert hierarchy.get_parent_level("municipality") == "province"
        assert hierarchy.get_parent_level("province") == "country"

    def test_get_parent_level_root_returns_none(self, hierarchy: GeoHierarchy) -> None:
        assert hierarchy.get_parent_level("country") is None

    def test_get_parent_level_invalid_level_raises(
        self, hierarchy: GeoHierarchy
    ) -> None:
        with pytest.raises(
            ValueError, match=r"level 'district' not found in hierarchy"
        ):
            hierarchy.get_parent_level("district")
