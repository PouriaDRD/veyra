# AGENTS.md

## Purpose

This file is the operating guide for coding agents working on Veyra.

Veyra is a modular social-profile discovery, validation, snapshot-intelligence,
hypothesis, and scoring engine. Preserve its clean architecture, deterministic
behavior, auditability, typing discipline, and explicit semantic boundaries.

## Core Product Eligibility Rule

Veyra's ranking/scoring target is confirmed-private profiles.

Privacy is a hard eligibility boundary, not a positive scoring feature:

- `is_private is True`: candidate may proceed through analysis and scoring.
- `is_private is False`: candidate must be excluded and must never receive a score.
- `is_private is None`: never assume private; candidate is unscorable until privacy is known.

Public profiles are not merely "lower weighted". They are outside the scoring
candidate set. No combination of occupation, education, institution, location,
profile-purpose, or other intelligence may override this rule.

The privacy guard must exist at scoring boundaries even if an earlier lifecycle
stage already filtered the candidate. Defense in depth is intentional.

Activity level, content interests/topics, and language are not primary ranking
features for the current product scope and must not be added to candidate
scoring unless product requirements explicitly change.

## Architecture

Primary dependency direction:

`Presentation -> Application -> Domain`

`Infrastructure -> Application ports / Domain`

The domain must not depend on SQLAlchemy, Alembic, Pydantic, HTTP frameworks,
database sessions, or infrastructure implementations.

## Intelligence Pipeline

`ProfileSnapshot`
`-> Privacy eligibility`
`-> Extractors`
`-> Evidence`
`-> Fact resolution`
`-> Validation / Filtering`
`-> Signals`
`-> Hypothesis Engine`
`-> Scoring`
`-> ScoreSnapshot audit`

Confirmed-public profiles should leave the candidate lifecycle as early as
practical and before scoring. Unknown privacy may remain available for later
resolution but cannot be scored.

Facts, signals, hypotheses, validation, filtering, and scoring are distinct
semantics. Do not encode filtering rejection as a low score.

## Scoring

A scoring feature value is normalized to `0..1`.

`effective_weight = weight * confidence`

`weighted_value = value * effective_weight`

`normalized_score = sum(weighted_value) / sum(effective_weight)`

`final_score = normalized_score * 10`

Missing information is omitted rather than treated as negative evidence.
A supported mismatch may contribute zero. No effective evidence means
unscorable (`None`), never an artificial zero.

Only confirmed-private analyses may reach feature adaptation and weighted
scoring.

Do not invent universal product weights. Weights belong to configured policy.

## Scoring Auditability

Every successful analysis-driven candidate score must preserve both:

1. `SearchCandidate.score`;
2. an immutable append-only `ScoreSnapshot`.

Candidate update and score-audit insertion share one Unit of Work transaction.

Unscorable, public, or unknown-privacy profiles must not create score snapshots.

## Evidence and Safety Semantics

Evidence keeps provenance, raw value, normalized value, confidence, nature,
strength, ambiguity, extractor identity, and observation time where applicable.

Do not infer sensitive personal traits from contextual proxies.

Do not implement attractiveness scoring.

Age must remain explicit/evidence-based. Uncertain age and minors belong to
validation/filtering policy, not speculative scoring.

Do not implement CAPTCHA bypass, stealth/evasion, anti-bot circumvention, or
access-control bypass.

## Multi-Value Facts

Education and institution can be multi-valued.

Compatible values must not become false conflicts.

Education and institution remain independent facts. Explicit relations are
modeled separately and must not be guessed across unrelated text segments.

## Correlation and Double Counting

Duplicate scoring keys are invalid but do not solve correlated evidence.

Do not silently count the same underlying evidence multiple times merely
because it appears as a fact, hypothesis, and relation.

## Text Normalization

Persian is first-class.

Normalization principles include NFKC, Arabic yeh/kaf normalization, ASCII
digit normalization, zero-width handling, whitespace collapse, and casefolding.

Preserve room for mixed Persian/English, Finglish, slang, and half-space.

## Persistence

Domain entities and SQLAlchemy models are separate. Use explicit mappers.

Repositories implement application ports and share one Unit of Work transaction.

Schema changes require Alembic migrations. After schema changes run:

```bat
alembic upgrade head
alembic check
```

Never rewrite an already-pushed migration unless explicitly repairing history.

## Typing and Style

Python 3.13+, strict mypy, Ruff formatting/linting.

Prefer precise types, immutable value objects/results, enums for closed sets,
protocols for ports, dependency injection, deterministic methods, and useful
docstrings.

Avoid hidden global state, domain-to-infrastructure imports, broad exception
swallowing, and magic business constants.

## Determinism

Given the same snapshot, privacy state, policy, ruleset, algorithm version, and
reference time, semantic results should be reproducible.

Sort externally observable unordered outputs. Version material algorithm/ruleset
changes.

## Testing Gate

For meaningful changes run targeted tests first, then:

```bat
pytest
mypy
ruff format --check .
ruff check .
alembic check
python -m veyra
```

Do not claim a gate is green unless it actually ran and passed.

Do not weaken tests to hide production bugs.

## Git Workflow

Primary development branch: `dev`.

Before editing existing files, inspect the current branch version.

Before commit:

```bat
git status --short
git diff --stat
git diff
```

After staging:

```bat
git status --short
git diff --cached --stat
git diff --cached
```

After push:

```bat
git rev-parse HEAD
git status
git log -1 --oneline
```

Windows CRLF warnings are not failures by themselves.

Keep diffs narrow and do not mix unrelated refactors into feature commits.

## Current Scoring Architecture

`ProfileAnalysisResult + AnalysisScoringPolicy`
`-> privacy eligibility guard`
`-> AnalysisScoringFeatureAdapter`
`-> tuple[ScoringFeature, ...]`
`-> WeightedScoringEngine`
`-> ScoreResult`
`-> SearchCandidate score + ScoreSnapshot audit`

Current scoring rules may use fact-value criteria, hypothesis-value criteria,
and explicit education/institution relation criteria, but only after confirmed
private eligibility.

## Definition of Done for New Intelligence Features

A permitted new intelligence feature should, where applicable, have a clear
path:

`evidence`
`-> fact / signal / hypothesis`
`-> scoring adapter/policy`
`-> score contribution`
`-> explanation / audit`

But not every analytics feature belongs in ranking. Activity level, content
topics/interests, and language are explicitly outside current core scoring
scope.

Include focused tests, deterministic behavior, provenance, and correct
confidence semantics.

## Agent Behavior

Before substantial changes:

1. inspect current implementation;
2. identify the owning layer;
3. preserve semantic boundaries;
4. write/update focused tests;
5. run the appropriate gate;
6. inspect the diff before commit.

If a requested change conflicts with these rules, preserve the architecture and
surface the tradeoff instead of silently adding debt.
