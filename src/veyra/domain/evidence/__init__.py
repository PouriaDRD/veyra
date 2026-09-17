"""Veyra evidence domain."""

from .birth_year import BirthYear, CalendarSystem
from .confidence import (
    combine_confidences,
    conflict_confidence,
)
from .entities import Evidence, Fact, FactValue
from .enums import (
    ConfidenceLevel,
    EvidenceSource,
    FactKind,
    FactStatus,
)
from .extractors import (
    BioBirthYearExtractor,
    UsernameBirthYearExtractor,
    normalize_digits,
)
from .resolver import FactResolver

__all__ = [
    "BioBirthYearExtractor",
    "BirthYear",
    "CalendarSystem",
    "ConfidenceLevel",
    "Evidence",
    "EvidenceSource",
    "Fact",
    "FactKind",
    "FactResolver",
    "FactStatus",
    "FactValue",
    "UsernameBirthYearExtractor",
    "combine_confidences",
    "conflict_confidence",
    "normalize_digits",
]
