"""Rule definitions for converting analysis output into scoring features."""

from dataclasses import dataclass

from veyra.domain.evidence import FactKind, FactValue
from veyra.domain.intelligence import HypothesisKind


def _normalize_text(
    value: str,
    *,
    field_name: str,
) -> str:
    """Strip and validate one required text field."""

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be empty.",
        )

    return normalized


def _validate_weight(
    value: float,
) -> float:
    """Validate one non-negative configured scoring weight."""

    if isinstance(value, bool):
        raise ValueError(
            "weight must be a non-negative numeric value.",
        )

    normalized = float(
        value,
    )

    if normalized < 0:
        raise ValueError(
            "weight must be non-negative.",
        )

    return normalized


@dataclass(frozen=True, slots=True)
class FactValueScoringRule:
    """Score whether one resolved fact matches an accepted value."""

    key: str
    kind: FactKind
    accepted_values: tuple[FactValue, ...]
    weight: float
    reason: str

    def __post_init__(self) -> None:
        """Normalize and validate fact-rule state."""

        if not self.accepted_values:
            raise ValueError(
                "accepted_values must not be empty.",
            )

        if len(set(self.accepted_values)) != len(self.accepted_values):
            raise ValueError(
                "accepted_values must be unique.",
            )

        object.__setattr__(
            self,
            "key",
            _normalize_text(
                self.key,
                field_name="key",
            ),
        )
        object.__setattr__(
            self,
            "weight",
            _validate_weight(
                self.weight,
            ),
        )
        object.__setattr__(
            self,
            "reason",
            _normalize_text(
                self.reason,
                field_name="reason",
            ),
        )


@dataclass(frozen=True, slots=True)
class HypothesisValueScoringRule:
    """Score support for one or more desired hypothesis values."""

    key: str
    kind: HypothesisKind
    accepted_values: tuple[str, ...]
    weight: float
    reason: str

    def __post_init__(self) -> None:
        """Normalize and validate hypothesis-rule state."""

        normalized_values = tuple(value.strip() for value in self.accepted_values)

        if not normalized_values:
            raise ValueError(
                "accepted_values must not be empty.",
            )

        if any(not value for value in normalized_values):
            raise ValueError(
                "accepted_values must not contain empty values.",
            )

        if len(set(normalized_values)) != len(normalized_values):
            raise ValueError(
                "accepted_values must be unique.",
            )

        object.__setattr__(
            self,
            "key",
            _normalize_text(
                self.key,
                field_name="key",
            ),
        )
        object.__setattr__(
            self,
            "accepted_values",
            normalized_values,
        )
        object.__setattr__(
            self,
            "weight",
            _validate_weight(
                self.weight,
            ),
        )
        object.__setattr__(
            self,
            "reason",
            _normalize_text(
                self.reason,
                field_name="reason",
            ),
        )


@dataclass(frozen=True, slots=True)
class EducationInstitutionScoringRule:
    """Score one explicit education-to-institution pair."""

    key: str
    education: str
    institution: str
    weight: float
    reason: str

    def __post_init__(self) -> None:
        """Normalize and validate relation-rule state."""

        object.__setattr__(
            self,
            "key",
            _normalize_text(
                self.key,
                field_name="key",
            ),
        )
        object.__setattr__(
            self,
            "education",
            _normalize_text(
                self.education,
                field_name="education",
            ).casefold(),
        )
        object.__setattr__(
            self,
            "institution",
            _normalize_text(
                self.institution,
                field_name="institution",
            ).casefold(),
        )
        object.__setattr__(
            self,
            "weight",
            _validate_weight(
                self.weight,
            ),
        )
        object.__setattr__(
            self,
            "reason",
            _normalize_text(
                self.reason,
                field_name="reason",
            ),
        )


@dataclass(frozen=True, slots=True)
class AnalysisScoringPolicy:
    """Immutable configured rules used to score one profile analysis."""

    fact_rules: tuple[
        FactValueScoringRule,
        ...,
    ] = ()

    hypothesis_rules: tuple[
        HypothesisValueScoringRule,
        ...,
    ] = ()

    relation_rules: tuple[
        EducationInstitutionScoringRule,
        ...,
    ] = ()

    def __post_init__(self) -> None:
        """Reject duplicate keys across all configured scoring rules."""

        fact_keys = tuple(rule.key for rule in self.fact_rules)

        hypothesis_keys = tuple(rule.key for rule in self.hypothesis_rules)

        relation_keys = tuple(rule.key for rule in self.relation_rules)

        keys = (
            *fact_keys,
            *hypothesis_keys,
            *relation_keys,
        )

        if len(set(keys)) != len(keys):
            raise ValueError(
                "scoring rule keys must be unique.",
            )
