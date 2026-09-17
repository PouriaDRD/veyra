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
    DEFAULT_OCCUPATION_LEXICON,
    BioBirthYearExtractor,
    BioEducationExtractor,
    BioEmployerExtractor,
    BioInstitutionExtractor,
    BioLocationExtractor,
    BioRelationshipStatusExtractor,
    EducationCredential,
    EducationLevel,
    OccupationEntry,
    OccupationLexicon,
    OccupationTextSource,
    ProfileOccupationExtractor,
    UsernameBirthYearExtractor,
    normalize_digits,
)
from .resolver import FactResolver

__all__ = [
    "DEFAULT_OCCUPATION_LEXICON",
    "BioBirthYearExtractor",
    "BioEducationExtractor",
    "BioEmployerExtractor",
    "BioInstitutionExtractor",
    "BioLocationExtractor",
    "BioRelationshipStatusExtractor",
    "BirthYear",
    "CalendarSystem",
    "ConfidenceLevel",
    "EducationCredential",
    "EducationLevel",
    "Evidence",
    "EvidenceSource",
    "Fact",
    "FactKind",
    "FactResolver",
    "FactStatus",
    "FactValue",
    "OccupationEntry",
    "OccupationLexicon",
    "OccupationTextSource",
    "ProfileOccupationExtractor",
    "UsernameBirthYearExtractor",
    "combine_confidences",
    "conflict_confidence",
    "normalize_digits",
]
