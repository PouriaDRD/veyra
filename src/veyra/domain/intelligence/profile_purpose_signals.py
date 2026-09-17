"""Multilingual source-aware profile-purpose signal extraction."""

import re
from dataclasses import dataclass
from typing import Literal

from .enums import (
    ProfilePurpose,
    ProfilePurposeSignalKind,
)
from .profile_purpose import ProfilePurposeSignal
from .text import normalize_text

ProfilePurposeTextSource = Literal[
    "bio",
    "display_name",
]

_ALLOWED_SOURCES = {
    "bio",
    "display_name",
}


# ============================================================
# PERSONAL
# ============================================================

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


# ============================================================
# PROFESSIONAL
# ============================================================

_PROFESSIONAL_ROLES = (
    # English
    "software engineer",
    "software developer",
    "business analyst",
    "data analyst",
    "product manager",
    "product designer",
    "graphic designer",
    "developer",
    "programmer",
    "engineer",
    "designer",
    "analyst",
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
    "تحلیلگر کسب و کار",
    "تحلیلگر داده",
    "مدیر محصول",
    "طراح محصول",
    "طراح گرافیک",
    "مهندس",
    "طراح",
    "تحلیلگر",
    "پزشک",
    "دکتر",
    "وکیل",
    "مدرس",
    "مشاور",
    "معمار",
    "عکاس",
)


# ============================================================
# CREATOR
# ============================================================

_CREATOR_MARKERS = (
    # English
    "content creator",
    "digital creator",
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
    "تولید کننده محتوا",
    "کریتور",
    "بلاگر",
    "ولاگر",
    "یوتیوبر",
    "استریمر",
    "اینفلوئنسر",
    "پادکستر",
)


# ============================================================
# BUSINESS
# ============================================================

# Strong commercial intent. These are useful even inside a biography because
# they describe the profile itself rather than merely mentioning a company or
# studying a business-related subject.
_STRONG_BUSINESS_MARKERS = (
    # English
    "online shop",
    "online store",
    "official shop",
    "official store",
    "shop now",
    "order via dm",
    "dm for order",
    "orders open",
    "place your order",
    # Persian
    "فروشگاه",
    "فروش آنلاین",
    "فروش اینترنتی",
    "ثبت سفارش",
    "سفارش از طریق دایرکت",
    "سفارش در دایرکت",
    "برای سفارش دایرکت",
)

# These tokens can identify a business when they are the profile/display name,
# but are too ambiguous in a biography:
#
#   "Business student"
#   "I work at Acme Company"
#   "Brand designer"
#
# Therefore they are display-name-only unless a stronger commercial marker is
# present elsewhere.
_DISPLAY_NAME_BUSINESS_MARKERS = (
    # English
    "shop",
    "store",
    "brand",
    "company",
    "business",
    # Persian
    "برند",
    "شرکت",
    "کسب و کار",
    "کسب‌وکار",
)


# ============================================================
# ORGANIZATION
# ============================================================

# Strong self-identifying organization phrases that are sufficiently specific
# to be useful even in biography text.
_STRONG_ORGANIZATION_MARKERS = (
    # English
    "nonprofit foundation",
    "non-profit foundation",
    "nonprofit organization",
    "non-profit organization",
    "nonprofit association",
    "non-profit association",
    "ngo",
    # Persian
    "بنیاد خیریه",
    "موسسه خیریه",
    "مؤسسه خیریه",
    "سازمان مردم نهاد",
    "سازمان مردم‌نهاد",
    "انجمن خیریه",
)

# Institutional nouns by themselves are meaningful in a profile/display name
# but not in arbitrary biography prose.
_DISPLAY_NAME_ORGANIZATION_MARKERS = (
    # English
    "foundation",
    "association",
    "organization",
    "university",
    "institute",
    "academy",
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

_OFFICIAL_PROFILE_PREFIXES = (
    # English
    "official account",
    "official page",
    "official profile",
    # Persian
    "صفحه رسمی",
    "پیج رسمی",
    "حساب رسمی",
    "اکانت رسمی",
)


# ============================================================
# REGEX UTILITIES
# ============================================================


def _phrase_pattern(
    phrase: str,
) -> str:
    """
    Build a Unicode-safe whole-phrase regex.

    Boundaries prevent matches inside longer words, for example:
    - shop inside shopify
    - store inside storehouse
    - designer inside designerly
    """

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
            return normalize_text(
                phrase,
            )

    return None


def _contains_any_phrase(
    text: str,
    phrases: tuple[str, ...],
) -> bool:
    """Return whether text contains any whole semantic phrase."""

    return (
        _find_first_phrase(
            text,
            phrases,
        )
        is not None
    )


def _find_official_organization_marker(
    text: str,
) -> str | None:
    """
    Detect self-identifying institutional biography language.

    Examples:
    - "Official account of Tehran University"
    - "صفحه رسمی دانشگاه تهران"

    A plain statement such as:
    - "Student at Tehran University"

    must not identify the profile itself as an organization.
    """

    organization_markers = (
        *_DISPLAY_NAME_ORGANIZATION_MARKERS,
        *_STRONG_ORGANIZATION_MARKERS,
    )

    for prefix in _OFFICIAL_PROFILE_PREFIXES:
        prefix_pattern = _phrase_pattern(
            prefix,
        )

        prefix_match = re.search(
            prefix_pattern,
            text,
            re.IGNORECASE,
        )

        if prefix_match is None:
            continue

        for marker in organization_markers:
            marker_pattern = _phrase_pattern(
                marker,
            )

            marker_match = re.search(
                marker_pattern,
                text,
                re.IGNORECASE,
            )

            if marker_match is None:
                continue

            return normalize_text(
                marker,
            )

    return None


# ============================================================
# EXTRACTOR
# ============================================================


@dataclass(frozen=True, slots=True)
class ProfilePurposeSignalExtractor:
    """
    Extract multilingual profile-purpose signals from public profile text.

    Extraction is source-aware.

    ``bio``:
        Uses conservative semantic interpretation. Generic words such as
        ``company``, ``business``, ``brand``, ``university`` and ``institute``
        do not classify the profile by themselves.

    ``display_name``:
        Can use broader identity-like markers because the display name usually
        describes the profile/entity itself more directly.

    The extractor emits signals only. Final inference remains the
    responsibility of the generic hypothesis engine.
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
        *,
        source: ProfilePurposeTextSource = "bio",
    ) -> tuple[ProfilePurposeSignal, ...]:
        """
        Extract purpose signals from one public profile text field.

        ``source`` must be either:
        - ``bio``
        - ``display_name``
        """

        normalized_source = source.strip()

        if normalized_source not in _ALLOWED_SOURCES:
            raise ValueError(
                "profile-purpose text source must be 'bio' or 'display_name'.",
            )

        normalized = normalize_text(
            text,
        )

        if not normalized:
            return ()

        signals: list[ProfilePurposeSignal] = []

        self._append_common_signals(
            signals,
            text=normalized,
        )

        self._append_business_signal(
            signals,
            text=normalized,
            source=normalized_source,
        )

        self._append_organization_signal(
            signals,
            text=normalized,
            source=normalized_source,
        )

        return tuple(
            signals,
        )

    def _append_common_signals(
        self,
        signals: list[ProfilePurposeSignal],
        *,
        text: str,
    ) -> None:
        """Extract source-independent purpose signals."""

        self._append_match(
            signals,
            text=text,
            phrases=_PERSONAL_MARKERS,
            kind=ProfilePurposeSignalKind.PERSONAL_MARKER,
            purpose=ProfilePurpose.PERSONAL,
            weight=self.personal_weight,
            confidence=self.personal_confidence,
        )

        self._append_match(
            signals,
            text=text,
            phrases=_PROFESSIONAL_ROLES,
            kind=ProfilePurposeSignalKind.PROFESSIONAL_ROLE,
            purpose=ProfilePurpose.PROFESSIONAL,
            weight=self.professional_weight,
            confidence=self.professional_confidence,
        )

        self._append_match(
            signals,
            text=text,
            phrases=_CREATOR_MARKERS,
            kind=ProfilePurposeSignalKind.CREATOR_MARKER,
            purpose=ProfilePurpose.CREATOR,
            weight=self.creator_weight,
            confidence=self.creator_confidence,
        )

    def _append_business_signal(
        self,
        signals: list[ProfilePurposeSignal],
        *,
        text: str,
        source: str,
    ) -> None:
        """Extract business intent without generic-word false positives."""

        strong_match = _find_first_phrase(
            text,
            _STRONG_BUSINESS_MARKERS,
        )

        if strong_match is not None:
            self._append_signal(
                signals,
                kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
                purpose=ProfilePurpose.BUSINESS,
                weight=self.business_weight,
                confidence=self.business_confidence,
                raw_value=strong_match,
                context=text,
            )

            return

        if source != "display_name":
            return

        display_name_match = _find_first_phrase(
            text,
            _DISPLAY_NAME_BUSINESS_MARKERS,
        )

        if display_name_match is None:
            return

        self._append_signal(
            signals,
            kind=ProfilePurposeSignalKind.BUSINESS_MARKER,
            purpose=ProfilePurpose.BUSINESS,
            weight=self.business_weight,
            confidence=self.business_confidence,
            raw_value=display_name_match,
            context=text,
        )

    def _append_organization_signal(
        self,
        signals: list[ProfilePurposeSignal],
        *,
        text: str,
        source: str,
    ) -> None:
        """Extract organization identity with source-aware semantics."""

        strong_match = _find_first_phrase(
            text,
            _STRONG_ORGANIZATION_MARKERS,
        )

        if strong_match is not None:
            self._append_signal(
                signals,
                kind=ProfilePurposeSignalKind.ORGANIZATION_MARKER,
                purpose=ProfilePurpose.ORGANIZATION,
                weight=self.organization_weight,
                confidence=self.organization_confidence,
                raw_value=strong_match,
                context=text,
            )

            return

        if source == "display_name":
            display_name_match = _find_first_phrase(
                text,
                _DISPLAY_NAME_ORGANIZATION_MARKERS,
            )

            if display_name_match is None:
                return

            self._append_signal(
                signals,
                kind=ProfilePurposeSignalKind.ORGANIZATION_MARKER,
                purpose=ProfilePurpose.ORGANIZATION,
                weight=self.organization_weight,
                confidence=self.organization_confidence,
                raw_value=display_name_match,
                context=text,
            )

            return

        official_match = _find_official_organization_marker(
            text,
        )

        if official_match is None:
            return

        self._append_signal(
            signals,
            kind=ProfilePurposeSignalKind.ORGANIZATION_MARKER,
            purpose=ProfilePurpose.ORGANIZATION,
            weight=self.organization_weight,
            confidence=self.organization_confidence,
            raw_value=official_match,
            context=text,
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
        """Append one signal when one phrase from a category matches."""

        matched = _find_first_phrase(
            text,
            phrases,
        )

        if matched is None:
            return

        ProfilePurposeSignalExtractor._append_signal(
            signals,
            kind=kind,
            purpose=purpose,
            weight=weight,
            confidence=confidence,
            raw_value=matched,
            context=text,
        )

    @staticmethod
    def _append_signal(
        signals: list[ProfilePurposeSignal],
        *,
        kind: ProfilePurposeSignalKind,
        purpose: ProfilePurpose,
        weight: float,
        confidence: float,
        raw_value: str,
        context: str,
    ) -> None:
        """Append one semantic category once."""

        if any(existing.kind is kind for existing in signals):
            return

        signals.append(
            ProfilePurposeSignal(
                kind=kind,
                purpose=purpose,
                weight=weight,
                confidence=confidence,
                raw_value=raw_value,
                context=context,
            )
        )
