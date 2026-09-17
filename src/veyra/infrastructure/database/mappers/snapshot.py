"""Profile snapshot persistence mapping."""

from veyra.domain.snapshots import ProfileSnapshot

from ..models import ProfileSnapshotModel


def snapshot_to_model(
    snapshot: ProfileSnapshot,
) -> ProfileSnapshotModel:
    """Map a ProfileSnapshot entity to its ORM representation."""

    return ProfileSnapshotModel(
        id=snapshot.id,
        profile_id=snapshot.profile_id,
        username=snapshot.username,
        display_name=snapshot.display_name,
        bio=snapshot.bio,
        followers_count=snapshot.followers_count,
        following_count=snapshot.following_count,
        posts_count=snapshot.posts_count,
        is_private=snapshot.is_private,
        is_verified=snapshot.is_verified,
        profile_picture_url=snapshot.profile_picture_url,
        captured_at=snapshot.captured_at,
    )


def snapshot_to_domain(
    model: ProfileSnapshotModel,
) -> ProfileSnapshot:
    """Reconstruct a ProfileSnapshot from its ORM representation."""

    return ProfileSnapshot(
        id=model.id,
        profile_id=model.profile_id,
        username=model.username,
        display_name=model.display_name,
        bio=model.bio,
        followers_count=model.followers_count,
        following_count=model.following_count,
        posts_count=model.posts_count,
        is_private=model.is_private,
        is_verified=model.is_verified,
        profile_picture_url=model.profile_picture_url,
        captured_at=model.captured_at,
    )
