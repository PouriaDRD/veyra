"""Profile domain persistence mapping."""

from veyra.domain.profiles import Profile, SocialPlatform

from ..models import ProfileModel


def profile_to_model(
    profile: Profile,
) -> ProfileModel:
    """Map a Profile domain entity to its ORM representation."""

    return ProfileModel(
        id=profile.id,
        platform=profile.platform.value,
        external_id=profile.external_id,
        username=profile.username,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def profile_to_domain(
    model: ProfileModel,
) -> Profile:
    """Reconstruct a Profile domain entity from its ORM representation."""

    return Profile(
        id=model.id,
        platform=SocialPlatform(model.platform),
        external_id=model.external_id,
        username=model.username,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
