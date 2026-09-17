"""Scoring domain enums."""

from enum import StrEnum


class ScoringSourceKind(StrEnum):
    """Semantic source feeding one scoring feature."""

    FACT = "fact"
    SIGNAL = "signal"
    HYPOTHESIS = "hypothesis"
    RELATION = "relation"
    DERIVED = "derived"
