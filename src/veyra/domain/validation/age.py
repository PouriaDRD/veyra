"""Adult age validation rules."""

from dataclasses import dataclass
from datetime import date

from veyra.domain.evidence import (
    BirthYear,
    CalendarSystem,
    Fact,
    FactKind,
    FactStatus,
)

from .entities import (
    ValidationFinding,
    ValidationResult,
)
from .enums import (
    ValidationCode,
    ValidationSeverity,
)


@dataclass(frozen=True, slots=True)
class AdultAgePolicy:
    """Configuration for adult-only age validation."""

    minimum_age: int = 18
    minimum_confidence: float = 0.7

    def __post_init__(self) -> None:
        """Validate policy values."""

        if self.minimum_age <= 0:
            raise ValueError(
                "minimum_age must be greater than zero.",
            )

        if not 0 <= self.minimum_confidence <= 1:
            raise ValueError(
                "minimum_confidence must be between 0 and 1.",
            )


class AdultAgeValidator:
    """
    Validate whether explicit age evidence establishes adulthood.

    Uncertain, conflicted, or insufficient evidence is rejected by default.
    """

    def __init__(
        self,
        policy: AdultAgePolicy | None = None,
    ) -> None:
        self._policy = policy if policy is not None else AdultAgePolicy()

    def validate(
        self,
        fact: Fact,
        *,
        reference_date: date,
    ) -> ValidationResult:
        """Validate one age or birth-year fact."""

        if fact.kind not in {
            FactKind.AGE,
            FactKind.BIRTH_YEAR,
        }:
            raise ValueError(
                "AdultAgeValidator requires an age or birth-year fact.",
            )

        if fact.status is FactStatus.UNKNOWN:
            return self._age_uncertain(
                confidence=0.0,
                message="Adult age could not be established.",
            )

        if fact.status is FactStatus.CONFLICTED:
            return ValidationResult(
                findings=(
                    ValidationFinding(
                        code=ValidationCode.CONFLICTING_EVIDENCE,
                        severity=ValidationSeverity.REJECT,
                        message="Age evidence contains conflicting values.",
                        confidence=fact.confidence,
                    ),
                    ValidationFinding(
                        code=ValidationCode.AGE_UNCERTAIN,
                        severity=ValidationSeverity.REJECT,
                        message="Adult age could not be established reliably.",
                        confidence=fact.confidence,
                    ),
                )
            )

        if fact.confidence < self._policy.minimum_confidence:
            return self._age_uncertain(
                confidence=fact.confidence,
                message=("Age evidence confidence is below the required threshold."),
            )

        if fact.kind is FactKind.AGE:
            age = self._require_exact_age(
                fact,
            )

            return self._validate_exact_age(
                age=age,
                confidence=fact.confidence,
            )

        birth_year = self._require_birth_year(
            fact,
        )

        return self._validate_birth_year(
            birth_year=birth_year,
            confidence=fact.confidence,
            reference_date=reference_date,
        )

    def _validate_exact_age(
        self,
        *,
        age: int,
        confidence: float,
    ) -> ValidationResult:
        """Validate an explicit exact-age fact."""

        if age < 0:
            raise ValueError(
                "Age must not be negative.",
            )

        if age < self._policy.minimum_age:
            return self._possible_minor(
                confidence=confidence,
            )

        return self._confirmed_adult(
            confidence=confidence,
        )

    def _validate_birth_year(
        self,
        *,
        birth_year: BirthYear,
        confidence: float,
        reference_date: date,
    ) -> ValidationResult:
        """Validate a calendar-aware birth year conservatively."""

        if birth_year.calendar is CalendarSystem.GREGORIAN:
            earliest_year = birth_year.year
            latest_year = birth_year.year

        elif birth_year.calendar is CalendarSystem.SOLAR_HIJRI:
            # A Solar Hijri year spans portions of two Gregorian years.
            # We intentionally use a conservative range here rather than
            # inventing an exact birthday.
            earliest_year = birth_year.year + 621
            latest_year = birth_year.year + 622

        else:
            raise ValueError(
                "Unsupported birth-year calendar.",
            )

        if earliest_year > reference_date.year:
            raise ValueError(
                "Birth year cannot be in the future.",
            )

        maximum_possible_age = reference_date.year - earliest_year

        minimum_possible_age = max(
            0,
            reference_date.year - latest_year - 1,
        )

        if maximum_possible_age < self._policy.minimum_age:
            return self._possible_minor(
                confidence=confidence,
            )

        if minimum_possible_age >= self._policy.minimum_age:
            return self._confirmed_adult(
                confidence=confidence,
            )

        return self._age_uncertain(
            confidence=confidence,
            message=(
                "Birth year alone does not establish whether "
                "the minimum adult age has already been reached."
            ),
        )

    @staticmethod
    def _require_exact_age(
        fact: Fact,
    ) -> int:
        """Return a supported exact integer age."""

        value = fact.value

        if isinstance(value, bool) or not isinstance(
            value,
            int,
        ):
            raise ValueError(
                "Age facts must resolve to an integer.",
            )

        return value

    @staticmethod
    def _require_birth_year(
        fact: Fact,
    ) -> BirthYear:
        """Return a supported calendar-aware birth year."""

        value = fact.value

        if not isinstance(
            value,
            BirthYear,
        ):
            raise ValueError(
                "Birth-year facts must resolve to BirthYear.",
            )

        return value

    @staticmethod
    def _age_uncertain(
        *,
        confidence: float,
        message: str,
    ) -> ValidationResult:
        """Return an uncertain-age rejection."""

        return ValidationResult(
            findings=(
                ValidationFinding(
                    code=ValidationCode.AGE_UNCERTAIN,
                    severity=ValidationSeverity.REJECT,
                    message=message,
                    confidence=confidence,
                ),
            )
        )

    @staticmethod
    def _possible_minor(
        *,
        confidence: float,
    ) -> ValidationResult:
        """Return a possible-minor rejection."""

        return ValidationResult(
            findings=(
                ValidationFinding(
                    code=ValidationCode.POSSIBLE_MINOR,
                    severity=ValidationSeverity.REJECT,
                    message=("Available explicit age evidence indicates a minor."),
                    confidence=confidence,
                ),
            )
        )

    @staticmethod
    def _confirmed_adult(
        *,
        confidence: float,
    ) -> ValidationResult:
        """Return a confirmed-adult result."""

        return ValidationResult(
            findings=(
                ValidationFinding(
                    code=ValidationCode.AGE_CONFIRMED_ADULT,
                    severity=ValidationSeverity.INFO,
                    message=("Explicit age evidence satisfies the adult-age requirement."),
                    confidence=confidence,
                ),
            )
        )
