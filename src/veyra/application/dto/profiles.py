"""Profile application data-transfer objects."""

from dataclasses import dataclass

from veyra.domain.profiles import SocialPlatform


@dataclass(frozen=True, slots=True)
class CreateProfileCommand:
    """Input required to register a discovered social profile."""

    platform: SocialPlatform
    external_id: str
    username: str
