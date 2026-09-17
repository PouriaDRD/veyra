"""Scoring audit persistence mapping."""

import json
from typing import Any

from veyra.domain.scoring import (
    ScoreContribution,
    ScoreSnapshot,
    ScoringSourceKind,
)

from ..models import ScoreSnapshotModel


def _contribution_to_payload(
    contribution: ScoreContribution,
) -> dict[str, Any]:
    """Serialize one explainable score contribution."""

    return {
        "key": contribution.key,
        "value": contribution.value,
        "configured_weight": contribution.configured_weight,
        "confidence": contribution.confidence,
        "effective_weight": contribution.effective_weight,
        "weighted_value": contribution.weighted_value,
        "reason": contribution.reason,
        "source_kind": contribution.source_kind.value,
        "source_key": contribution.source_key,
    }


def _contribution_from_payload(
    payload: dict[str, Any],
) -> ScoreContribution:
    """Reconstruct one score contribution from persisted JSON."""

    return ScoreContribution(
        key=str(payload["key"]),
        value=float(payload["value"]),
        configured_weight=float(payload["configured_weight"]),
        confidence=float(payload["confidence"]),
        effective_weight=float(payload["effective_weight"]),
        weighted_value=float(payload["weighted_value"]),
        reason=str(payload["reason"]),
        source_kind=ScoringSourceKind(
            str(payload["source_kind"]),
        ),
        source_key=(str(payload["source_key"]) if payload.get("source_key") is not None else None),
    )


def score_snapshot_to_model(
    snapshot: ScoreSnapshot,
) -> ScoreSnapshotModel:
    """Map a score audit snapshot to its ORM representation."""

    contributions_json = json.dumps(
        [
            _contribution_to_payload(
                contribution,
            )
            for contribution in snapshot.contributions
        ],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )

    return ScoreSnapshotModel(
        id=snapshot.id,
        candidate_id=snapshot.candidate_id,
        profile_snapshot_id=snapshot.profile_snapshot_id,
        score=snapshot.score,
        normalized_value=snapshot.normalized_value,
        total_effective_weight=snapshot.total_effective_weight,
        algorithm_version=snapshot.algorithm_version,
        contributions_json=contributions_json,
        created_at=snapshot.created_at,
    )


def score_snapshot_to_domain(
    model: ScoreSnapshotModel,
) -> ScoreSnapshot:
    """Reconstruct a score audit snapshot from persistence."""

    raw_payload = json.loads(
        model.contributions_json,
    )

    if not isinstance(raw_payload, list):
        raise ValueError(
            "score snapshot contributions payload must be a list.",
        )

    contributions = tuple(
        _contribution_from_payload(
            payload,
        )
        for payload in raw_payload
        if isinstance(payload, dict)
    )

    if len(contributions) != len(raw_payload):
        raise ValueError(
            "score snapshot contributions payload contains invalid entries.",
        )

    return ScoreSnapshot(
        id=model.id,
        candidate_id=model.candidate_id,
        profile_snapshot_id=model.profile_snapshot_id,
        score=model.score,
        normalized_value=model.normalized_value,
        total_effective_weight=model.total_effective_weight,
        algorithm_version=model.algorithm_version,
        contributions=contributions,
        created_at=model.created_at,
    )
