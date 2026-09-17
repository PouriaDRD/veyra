"""Profile analysis data-transfer objects."""

from dataclasses import dataclass
from uuid import UUID

from veyra.domain.evidence import (
    Evidence,
    Fact,
    FactKind,
)
from veyra.domain.intelligence import (
    HypothesisKind,
    HypothesisObservation,
    HypothesisResult,
)
from veyra.domain.validation import ValidationResult


@dataclass(frozen=True, slots=True)
class ProfileAnalysisResult:
    """
    Explainable result of analyzing one immutable profile snapshot.

    The result keeps:
    - extracted evidence
    - resolved facts
    - normalized hypothesis observations
    - derived hypotheses
    - validation findings

    This allows filtering, scoring, persistence, and presentation layers to
    consume one coherent analysis result without reconstructing context.
    """

    snapshot_id: UUID
    profile_id: UUID

    evidence: tuple[Evidence, ...]
    facts: tuple[Fact, ...]

    observations: tuple[
        HypothesisObservation,
        ...,
    ]

    hypotheses: tuple[
        HypothesisResult,
        ...,
    ]

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

    def hypothesis_for(
        self,
        kind: HypothesisKind,
    ) -> HypothesisResult | None:
        """Return the derived hypothesis for one kind when present."""

        for hypothesis in self.hypotheses:
            if hypothesis.kind is kind:
                return hypothesis

        return None
