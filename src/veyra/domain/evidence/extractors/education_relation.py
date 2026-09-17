"""Explicit education-to-institution relationship extraction."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from veyra.domain.common import ensure_utc_datetime, utc_now
from veyra.domain.intelligence import EvidenceNature, EvidenceStrength, normalize_text

from ..enums import EvidenceSource
from .education import BioEducationExtractor, BioInstitutionExtractor

_SEGMENT_SPLIT_PATTERN = re.compile(r"[\n|•;,،]+")


@dataclass(frozen=True, slots=True)
class EducationInstitutionRelation:
    """One explicit education credential linked to one explicit institution."""

    education: str
    institution: str
    raw_value: str
    confidence: float
    source: EvidenceSource = EvidenceSource.BIO
    nature: EvidenceNature = EvidenceNature.EXPLICIT
    strength: EvidenceStrength = EvidenceStrength.VERY_STRONG
    id: UUID = field(default_factory=uuid4)
    observed_at: datetime = field(default_factory=utc_now)
    extractor: str = "bio_education_institution_explicit"

    def __post_init__(self) -> None:
        education = normalize_text(self.education).strip()
        institution = normalize_text(self.institution).strip()
        raw_value = self.raw_value.strip()

        if not education:
            raise ValueError("education must not be empty.")
        if not institution:
            raise ValueError("institution must not be empty.")
        if not raw_value:
            raise ValueError("raw_value must not be empty.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1.")

        object.__setattr__(self, "education", education)
        object.__setattr__(self, "institution", institution)
        object.__setattr__(self, "raw_value", raw_value)
        object.__setattr__(
            self,
            "observed_at",
            ensure_utc_datetime(self.observed_at, field_name="observed_at"),
        )


class BioEducationInstitutionRelationExtractor:
    """Extract explicit same-segment education/institution relationships."""

    def __init__(
        self,
        *,
        education_extractor: BioEducationExtractor | None = None,
        institution_extractor: BioInstitutionExtractor | None = None,
    ) -> None:
        self._education_extractor = education_extractor or BioEducationExtractor()
        self._institution_extractor = institution_extractor or BioInstitutionExtractor()

    def extract(self, text: str) -> tuple[EducationInstitutionRelation, ...]:
        if not text.strip():
            return ()

        relations: list[EducationInstitutionRelation] = []
        seen_pairs: set[tuple[str, str]] = set()

        for raw_segment in _SEGMENT_SPLIT_PATTERN.split(text):
            segment = normalize_text(
                raw_segment,
            ).strip()

            if not segment:
                continue

            education_evidence = self._education_extractor.extract(segment)
            institution_evidence = self._institution_extractor.extract(segment)

            education_values = {str(item.normalized_value) for item in education_evidence}
            institution_values = {str(item.normalized_value) for item in institution_evidence}

            if len(education_values) != 1 or len(institution_values) != 1:
                continue

            education = next(iter(education_values))
            institution = next(iter(institution_values))
            pair = (education, institution)

            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            confidence = min(
                item.confidence
                for item in (*education_evidence, *institution_evidence)
                if str(item.normalized_value) in pair
            )

            relations.append(
                EducationInstitutionRelation(
                    education=education,
                    institution=institution,
                    raw_value=segment,
                    confidence=confidence,
                )
            )

        return tuple(
            sorted(
                relations,
                key=lambda relation: (relation.education, relation.institution),
            )
        )
