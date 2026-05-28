"""Constraint taxonomy types (CDL — Constraint Detection Layer)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .parser import ParseResult


class ConstraintType(Enum):
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    TEMPORAL = "temporal"
    HUMAN = "human"
    SEMANTIC = "semantic"
    INTEGRATION = "integration"
    EMERGENT = "emergent"


class ConstraintCategory(Enum):
    HARD = "hard"
    SOFT = "soft"
    FALSE = "false"


class ConstraintLevel(Enum):
    FEDERATION = "federation"
    GUILD = "guild"
    AGENT = "agent"
    ENTRY_POINT = "entry_point"


@dataclass
class Constraint:
    raw_text: str
    constraint_type: ConstraintType
    constraint_category: ConstraintCategory
    quantifiable: bool = False
    relaxable: bool = False
    priority: int = 5


def _categorize_by_kind(kind: str) -> ConstraintCategory:
    hard_kinds = {"requirement", "exact", "dependency", "negation"}
    false_kinds = {"assumption"}
    if kind in hard_kinds:
        return ConstraintCategory.HARD
    if kind in false_kinds:
        return ConstraintCategory.FALSE
    return ConstraintCategory.SOFT


def _type_for_kind(kind: str) -> ConstraintType:
    kind_type_map: dict[str, ConstraintType] = {
        "exact": ConstraintType.SEMANTIC,
        "requirement": ConstraintType.TECHNICAL,
        "negation": ConstraintType.SEMANTIC,
        "dependency": ConstraintType.INTEGRATION,
        "assumption": ConstraintType.EMERGENT,
        "conditional": ConstraintType.SEMANTIC,
    }
    return kind_type_map.get(kind, ConstraintType.TECHNICAL)


def upgrade_constraints(result: ParseResult) -> list[Constraint]:
    """Upgrade parser's raw constraint kind strings to typed Constraint objects."""
    typed: list[Constraint] = []
    for kind in result.constraints:
        ctype = _type_for_kind(kind)
        cat = _categorize_by_kind(kind)
        quant = kind in ("exact",)
        relax = kind in ("conditional",)
        typed.append(
            Constraint(
                raw_text=kind,
                constraint_type=ctype,
                constraint_category=cat,
                quantifiable=quant,
                relaxable=relax,
            )
        )
    return typed


@dataclass
class ConstraintAnalysis:
    typed: list[Constraint] = field(default_factory=list)
    hard_count: int = 0
    soft_count: int = 0
    false_count: int = 0
    missing_types: list[ConstraintType] = field(default_factory=list)

    @classmethod
    def from_parse(cls, result: ParseResult) -> ConstraintAnalysis:
        typed = upgrade_constraints(result)
        hard = sum(1 for c in typed if c.constraint_category == ConstraintCategory.HARD)
        soft = sum(1 for c in typed if c.constraint_category == ConstraintCategory.SOFT)
        false = sum(1 for c in typed if c.constraint_category == ConstraintCategory.FALSE)
        found_types = {c.constraint_type for c in typed}
        missing = [t for t in ConstraintType if t not in found_types]
        return cls(typed=typed, hard_count=hard, soft_count=soft, false_count=false, missing_types=missing)
