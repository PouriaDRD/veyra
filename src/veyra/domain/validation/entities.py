"""Validation result domain entities."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .enums import ValidationCode, ValidationSeverity


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """One explainable validation finding."""

    code: ValidationCode
    severity: ValidationSeverity
    message: str

    confidence: float | None = None

    id: UUID = field(
        default_factory=uuid4,
    )

    def __post_init__(self) -> None:
        """Validate finding state."""

        message = self.message.strip()

        if not message:
            raise ValueError(
                "message must not be empty.",
            )

        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1.",
            )

        object.__setattr__(
            self,
            "message",
            message,
        )


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Aggregate validation outcome.

    A rejected result contains at least one REJECT-level finding.
    """

    findings: tuple[ValidationFinding, ...]

    def __post_init__(self) -> None:
        """Validate aggregate state."""

        if not self.findings:
            raise ValueError(
                "validation result must contain at least one finding.",
            )

    @property
    def is_accepted(self) -> bool:
        """Return whether the candidate survives validation."""

        return not any(finding.severity is ValidationSeverity.REJECT for finding in self.findings)

    @property
    def rejection_codes(
        self,
    ) -> tuple[ValidationCode, ...]:
        """Return machine-readable rejection reasons."""

        return tuple(
            finding.code
            for finding in self.findings
            if finding.severity is ValidationSeverity.REJECT
        )

    def has_code(
        self,
        code: ValidationCode,
    ) -> bool:
        """Return whether one finding uses the requested code."""

        return any(finding.code is code for finding in self.findings)

    @classmethod
    def combine(
        cls,
        results: Iterable["ValidationResult"],
    ) -> "ValidationResult":
        """Combine multiple validator outputs into one aggregate result."""

        findings = tuple(finding for result in results for finding in result.findings)

        if not findings:
            raise ValueError(
                "at least one validation result is required.",
            )

        return cls(
            findings=findings,
        )
