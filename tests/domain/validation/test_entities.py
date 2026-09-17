"""Tests for validation result entities."""

import pytest

from veyra.domain.validation import (
    ValidationCode,
    ValidationFinding,
    ValidationResult,
    ValidationSeverity,
)


def test_validation_result_accepts_non_reject_findings() -> None:
    result = ValidationResult(
        findings=(
            ValidationFinding(
                code=ValidationCode.AGE_CONFIRMED_ADULT,
                severity=ValidationSeverity.INFO,
                message="Explicit evidence confirms adult age.",
                confidence=0.95,
            ),
        )
    )

    assert result.is_accepted is True
    assert result.rejection_codes == ()


def test_validation_result_rejects_possible_minor() -> None:
    result = ValidationResult(
        findings=(
            ValidationFinding(
                code=ValidationCode.POSSIBLE_MINOR,
                severity=ValidationSeverity.REJECT,
                message="Available age evidence may indicate a minor.",
                confidence=0.85,
            ),
        )
    )

    assert result.is_accepted is False

    assert result.rejection_codes == (ValidationCode.POSSIBLE_MINOR,)


def test_age_uncertain_can_be_rejected_explicitly() -> None:
    result = ValidationResult(
        findings=(
            ValidationFinding(
                code=ValidationCode.AGE_UNCERTAIN,
                severity=ValidationSeverity.REJECT,
                message="Adult age could not be established.",
            ),
        )
    )

    assert result.is_accepted is False


def test_validation_finding_rejects_invalid_confidence() -> None:
    with pytest.raises(
        ValueError,
        match="confidence must be between 0 and 1",
    ):
        ValidationFinding(
            code=ValidationCode.LOCATION_CONFIRMED,
            severity=ValidationSeverity.INFO,
            message="Location confirmed.",
            confidence=-0.1,
        )


def test_validation_result_requires_findings() -> None:
    with pytest.raises(
        ValueError,
        match="must contain at least one finding",
    ):
        ValidationResult(
            findings=(),
        )
