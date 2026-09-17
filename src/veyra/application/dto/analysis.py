"""Profile analysis data-transfer objects."""

from dataclasses import dataclass
from uuid import UUID

from veyra.domain.evidence import (
    Evidence,
    Fact,
    FactKind,
)
from veyra.domain.validation import ValidationResult


@dataclass(frozen=True, slots=True)
class ProfileAnalysisResult:
    """
    Explainable result of analyzing one immutable profile snapshot.

    The result keeps raw evidence, resolved facts, and validation findings
    together so later filtering, scoring, persistence, and presentation
    layers do not need to reconstruct analysis context.
    """

    snapshot_id: UUID
    profile_id: UUID

    evidence: tuple[Evidence, ...]
    facts: tuple[Fact, ...]

    validation: ValidationResult

    def fact_for(
        self,
        kind: FactKind,
    ) -> Fact | None:
        """Return the resolved fact for one kind when present."""

        for fact in self.facts:
            if fact.kind is kind:
                return fact

        return None
