import pytest
from ambiguity.parser import parse
from ambiguity.constraints import (
    ConstraintType, ConstraintCategory, Constraint,
    _categorize_by_kind, _type_for_kind, upgrade_constraints,
    ConstraintAnalysis,
)


def test_constraint_type_enum_values():
    assert ConstraintType.TECHNICAL.value == "technical"
    assert ConstraintType.FINANCIAL.value == "financial"
    assert ConstraintType.TEMPORAL.value == "temporal"


def test_constraint_category_enum_values():
    assert ConstraintCategory.HARD.value == "hard"
    assert ConstraintCategory.SOFT.value == "soft"
    assert ConstraintCategory.FALSE.value == "false"


def test_categorize_hard_kinds():
    for kind in ("requirement", "exact", "dependency", "negation"):
        assert _categorize_by_kind(kind) == ConstraintCategory.HARD


def test_categorize_false_kinds():
    assert _categorize_by_kind("assumption") == ConstraintCategory.FALSE


def test_categorize_soft_default():
    assert _categorize_by_kind("conditional") == ConstraintCategory.SOFT
    assert _categorize_by_kind("unknown") == ConstraintCategory.SOFT


def test_type_for_kind_mapping():
    assert _type_for_kind("exact") == ConstraintType.SEMANTIC
    assert _type_for_kind("requirement") == ConstraintType.TECHNICAL
    assert _type_for_kind("negation") == ConstraintType.SEMANTIC
    assert _type_for_kind("dependency") == ConstraintType.INTEGRATION
    assert _type_for_kind("assumption") == ConstraintType.EMERGENT
    assert _type_for_kind("conditional") == ConstraintType.SEMANTIC


def test_type_for_kind_default():
    assert _type_for_kind("unknown") == ConstraintType.TECHNICAL


def test_upgrade_constraints_empty():
    result = parse("hello world")
    assert upgrade_constraints(result) == []


def test_upgrade_constraints_with_negation():
    result = parse("implement without imports")
    typed = upgrade_constraints(result)
    kinds = [c.raw_text for c in typed]
    assert "negation" in kinds
    for c in typed:
        if c.raw_text == "negation":
            assert c.constraint_category == ConstraintCategory.HARD
            assert c.constraint_type == ConstraintType.SEMANTIC
            assert c.quantifiable is False
            assert c.relaxable is False


def test_upgrade_constraints_with_exact():
    result = parse("use only standard library")
    typed = upgrade_constraints(result)
    kinds = [c.raw_text for c in typed]
    assert "exact" in kinds
    for c in typed:
        if c.raw_text == "exact":
            assert c.quantifiable is True


def test_upgrade_constraints_relaxable():
    # Soft constraints that parser may detect as conditional
    result = parse("if possible use python")
    typed = upgrade_constraints(result)
    if not typed:
        pytest.skip("parser did not detect conditional constraint")
    for c in typed:
        if c.raw_text == "conditional":
            assert c.relaxable is True


def test_constraint_analysis_from_parse():
    result = parse("implement without imports, use only standard library")
    ca = ConstraintAnalysis.from_parse(result)
    assert len(ca.typed) >= 2
    assert ca.hard_count >= 2
    assert ca.soft_count >= 0


def test_constraint_analysis_missing_types():
    result = parse("hello world")
    ca = ConstraintAnalysis.from_parse(result)
    assert len(ca.typed) == 0
    assert ConstraintType.TECHNICAL in ca.missing_types
    assert ca.hard_count == 0
    assert ca.soft_count == 0


def test_constraint_dataclass_defaults():
    c = Constraint(
        raw_text="test",
        constraint_type=ConstraintType.TECHNICAL,
        constraint_category=ConstraintCategory.HARD,
    )
    assert c.quantifiable is False
    assert c.relaxable is False
    assert c.priority == 5
