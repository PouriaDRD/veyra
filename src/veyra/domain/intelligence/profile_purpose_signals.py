"""Multilingual profile-purpose signal extraction."""

import re
from dataclasses import dataclass

from .enums import (
    ProfilePurpose,
    ProfilePurposeSignalKind,
)
from .profile_purpose import ProfilePurposeSignal
from .text import normalize_text

_PERSONAL_MARKERS = (
    # English
    "personal account",
    "personal profile",
    "my personal life",
    "my life",
    # Persian
    "پیج شخصی",
    "صفحه شخصی",
    "زندگی شخصی",
    "روزمرگی",
    "روزمره",
)

_PROFESSIONAL_ROLES = (
    # English
    "software engineer",
    "software developer",
    "developer",
    "programmer",
    "engineer",
    "designer",
    "graphic designer",
    "product designer",
    "doctor",
    "physician",
    "lawyer",
    "teacher",
    "consultant",
    "architect",
    "photographer",
    # Persian
    "مهندس نرم افزار",
    "توسعه دهنده",
    "برنامه نویس",
    "مهندس",
    "طراح",
    "طراح گرافیک",
    "پزشک",
    "دکتر",
    "وکیل",
    "مدرس",
    "مشاور",
    "معمار",
    "عکاس",
)

_CREATOR_MARKERS = (
    # English
    "content creator",
    "creator",
    "blogger",
    "vlogger",
    "youtuber",
    "streamer",
    "influencer",
    "podcaster",
    # Persian
    "تولید محتوا",
    "تولیدکننده محتوا",
    "بلاگر",
    "ولاگر",
    "یوتیوبر",
    "استریمر",
    "اینفلوئنسر",
    "پادکستر",
)

_BUSINESS_MARKERS = (
    # English
    "online shop",
    "online store",
    "shop",
    "store",
    "brand",
    "company",
    "business",
    "order via dm",
    "dm for order",
    "orders open",
    # Persian
    "فروشگاه",
    "فروش آنلاین",
    "فروش اینترنتی",
    "ثبت سفارش",
    "سفارش",
    "خرید",
    "برند",
    "شرکت",
    "کسب و کار",
    "کسب‌وکار",
)

_ORGANIZATION_MARKERS = (
    # English
    "nonprofit",
    "non-profit",
    "foundation",
    "association",
    "organization",
    "university",
    "institute",
    "academy",
    "ngo",
    # Persian
    "سازمان",
    "موسسه",
    "مؤسسه",
    "بنیاد",
    "انجمن",
    "دانشگاه",
    "آکادمی",
    "خیریه",
)


def _phrase_pattern(
    phrase: str,
) -> str:
    """Build a Unicode-safe whole-phrase regex."""

    normalized = normalize_text(
        phrase,
    )

    if not normalized:
        raise ValueError(
            "profile-purpose phrase must not be empty.",
        )

    escaped = re.escape(
        normalized,
    ).replace(
        r"\ ",
        r"\s+",
    )

    return rf"(?<!\w)" rf"{escaped}" rf"(?!\w)"


def _find_first_phrase(
    text: str,
    phrases: tuple[str, ...],
) -> str | None:
    """Return the first matching normalized semantic phrase."""

    for phrase in phrases:
        pattern = _phrase_pattern(
            phrase,
        )

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return phrase

    return None


@dataclass(frozen=True, slots=True)
class ProfilePurposeSignalExtractor:
    """
    Extract multilingual profile-purpose signals from public profile text.

    This extractor is deliberately conservative.

    It emits normalized purpose signals from recognizable semantic markers
    but does not resolve the final profile purpose itself.

    Final inference is delegated to the generic hypothesis engine.
    """

    personal_weight: float = 0.85
    personal_confidence: float = 0.95

    professional_weight: float = 0.65
    professional_confidence: float = 0.90

    creator_weight: float = 0.85
    creator_confidence: float = 0.95

    business_weight: float = 0.90
    business_confidence: float = 0.95

    organization_weight: float = 0.90
    organization_confidence: float = 0.95

    def __post_init__(self) -> None:
        """Validate configured weights and confidence values."""

        values = (
            self.personal_weight,
            self.personal_confidence,
            self.professional_weight,
            self.professional_confidence,
            self.creator_weight,
            self.creator_confidence,
            self.business_weight,
            self.business_confidence,
            self.organization_weight,
            self.organization_confidence,
        )

        if any(not 0 <= value <= 1 for value in values):
            raise ValueError(
                "profile-purpose weights and confidence must be between 0 and 1.",
            )

    def extract(
        self,
        text: str,
    ) -> tuple[ProfilePurposeSignal, ...]:
        """Extract purpose signals from one public text field."""

        normalized = normalize_text(
            text,
        )

        if not normalized:
            return ()

        signals: list[ProfilePurposeSignal] = []

        self._append_match(
            signals,
            text=normalized,
            phrases=_PERSONAL_MARKERS,
            kind=ProfilePurposeSignalKind.PERSONAL_MARKER,
            purpose=ProfilePurpose.PERSONAL,
            weight=self.personal_weight,
            confidence=self.personal_confidence,
        )

        self._append_match(
            signals,
            text=normalized,
            phrases=_PROFESSIONAL_ROLES,
            kind=ProfilePurposeSignalKind.PROFESSIONAL_ROLE,
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=self.professional_weight,
            confidence=self.professional_confidence,
        )

        self._append_match(
            signals,
            text=normalized,
            phrases=_CREATOR_MARKERS,
            kind=ProfilePurposeSignalKind.CREATOR_MARKER,
            purpose=ProfilePurpose.CREATOR,
            weight=self.creator_weight,
            confidence=self.creator_confidence,
        )

        self._append_match(
            signals,
            text=normalized,
            phrases=_BUSINESS_MARKERS,
            kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
            purpose=ProfilePurpose.BUSINESS,
            weight=self.business_weight,
            confidence=self.business_confidence,
        )

        self._append_match(
            signals,
            text=normalized,
            phrases=_ORGANIZATION_MARKERS,
            kind=ProfilePurposeSignalKind.ORGANIZATION_MARKER,
            purpose=ProfilePurpose.ORGANIZATION,
            weight=self.organization_weight,
            confidence=self.organization_confidence,
        )

        return tuple(
            signals,
        )

    @staticmethod
    def _append_match(
        signals: list[ProfilePurposeSignal],
        *,
        text: str,
        phrases: tuple[str, ...],
        kind: ProfilePurposeSignalKind,
        purpose: ProfilePurpose,
        weight: float,
        confidence: float,
    ) -> None:
        """Append one signal when one phrase from the category matches."""

        matched = _find_first_phrase(
            text,
            phrases,
        )

        if matched is None:
            return

        signals.append(
            ProfilePurposeSignal(
                kind=kind,
                purpose=purpose,
                weight=weight,
                confidence=confidence,
                raw_value=matched,
                context=text,
            )
        )
