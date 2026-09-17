# AGENTS.md

## Purpose

This file is the operating guide for coding agents working on Veyra.

Veyra is a modular social-profile discovery, validation, snapshot-intelligence,
hypothesis, and scoring engine. Preserve its clean architecture, deterministic
behavior, auditability, typing discipline, and explicit semantic boundaries.

Do not treat this repository as a generic CRUD application. Domain semantics,
evidence provenance, scoring explainability, and reproducibility are core
requirements.

## Runtime and Toolchain

- Python: 3.13+
- Package layout: `src/`
- SQLAlchemy: 2.x
- Alembic: migrations
- Pytest: tests
- Mypy: strict mode
- Ruff: linting and formatting
- Structlog: structured logging
- Default local persistence: SQLite
- Production architecture must remain portable to PostgreSQL.

The canonical project configuration is `pyproject.toml`.

## Repository Layout

Primary boundaries:

- `src/veyra/domain/`
  Pure business and intelligence semantics.
- `src/veyra/application/`
  Use cases, DTOs, orchestration, ports, and policy adapters.
- `src/veyra/infrastructure/`
  Database, repositories, external implementations, and persistence mapping.
- `src/veyra/bootstrap/`
  Application composition and lifecycle.
- `tests/`
  Mirrors the application/domain/infrastructure boundaries.
- `migrations/`
  Alembic migrations.

Dependency direction:

`Presentation -> Application -> Domain`

`Infrastructure -> Application ports / Domain`

The domain must not depend on SQLAlchemy, Alembic, Pydantic, HTTP frameworks,
database sessions, or infrastructure implementations.

## Intelligence Pipeline

The conceptual flow is:

`Raw public profile`
`-> ProfileSnapshot`
`-> Extractors`
`-> Evidence`
`-> Fact resolution`
`-> Validation / Filtering`
`-> Signals / Features`
`-> Hypothesis Engine`
`-> Hypotheses / Analytics`
`-> Scoring`
`-> Explanation / Audit`

Keep these stages semantically distinct.

### Facts

Facts represent resolved claims supported by evidence.

Facts are not scoring preferences.

### Signals

Signals represent observations useful for inference.

Signals are not facts.

### Hypotheses

Hypotheses combine signals through the generic hypothesis engine.

Probability/support is not the same thing as evidence confidence.

### Validation and Filtering

Validation determines whether profile data satisfies validity/policy rules.

Filtering determines whether a candidate remains eligible.

Do not encode filtering rejection as a low score.

### Scoring

Scoring evaluates configured criteria.

A feature value is normalized to `0..1`.

Configured weight controls importance.

Confidence scales influence:

`effective_weight = weight * confidence`

`weighted_value = value * effective_weight`

`normalized_score = sum(weighted_value) / sum(effective_weight)`

`final_score = normalized_score * 10`

Missing or unresolved information is omitted rather than treated as negative
evidence.

A known supported mismatch may contribute a value of `0`.

If there is no effective scoring evidence, the result is unscorable (`None`);
never invent a zero score.

## Scoring Auditability

Every successful analysis-driven candidate scoring run must preserve both:

1. the normalized score on `SearchCandidate`;
2. an immutable append-only `ScoreSnapshot`.

`ScoreSnapshot` records:

- candidate identity;
- source profile snapshot identity;
- final score;
- normalized value;
- total effective weight;
- scoring algorithm version;
- full contribution breakdown;
- creation time.

Candidate score update and score-audit insertion must occur in the same Unit of
Work transaction.

Do not update or overwrite historical score snapshots.

Unscorable results must not create score snapshots.

## Evidence and Sensitive-Trait Rules

Use only public/profile-derived evidence supported by the product rules.

Do not infer sensitive personal traits from weak/contextual proxies.

In particular:

- do not infer personal religion or religiosity from religious content cues;
- do not infer protected/sensitive traits for personal scoring;
- do not use sensitive-trait proxies in scoring;
- explicit self-declared statements may be represented only when the domain
  explicitly supports them;
- content-level topics are distinct from personal identity.

Do not implement attractiveness scoring.

Age must remain explicit/evidence-based. Uncertain age and minors are subject to
validation/filtering policy, not speculative scoring.

Do not implement CAPTCHA bypass, stealth/evasion, anti-bot circumvention, or
other access-control bypass techniques.

## Evidence Semantics

Evidence must retain provenance.

Relevant concepts include:

- source;
- raw value;
- normalized value;
- confidence;
- evidence nature;
- evidence strength;
- ambiguity;
- extractor identity;
- observation time.

Do not discard raw evidence when normalization occurs.

## Multi-Value Facts

Some facts are intentionally multi-valued, notably education and institution.

Do not turn multiple compatible education/institution values into false
conflicts.

Education and institution remain independent facts.

Explicit education/institution relations are modeled separately and must not be
guessed across unrelated text segments.

## Correlation and Double Counting

Duplicate feature keys are invalid.

That does not by itself solve correlated evidence.

When multiple scoring features originate from the same underlying evidence,
consider correlation and double-counting risk explicitly.

Do not silently count the same evidence multiple times merely because it can be
represented as a fact, hypothesis, and relation.

## Text Normalization

Persian is a first-class language.

Current normalization principles include:

- Unicode NFKC;
- Arabic yeh/kaf normalization to Persian forms;
- digit normalization to ASCII;
- zero-width character handling;
- whitespace collapse;
- case folding.

Preserve room for mixed Persian/English, Finglish, slang, and half-space
handling.

## Persistence Rules

Domain entities and SQLAlchemy models are separate.

Use explicit mappers.

Repositories implement application-layer protocols.

All repositories participating in one use case should share one Unit of Work
transaction.

SQLite settings and behavior must not leak into domain semantics.

Schema changes require Alembic migrations.

After a schema change:

1. run `alembic upgrade head`;
2. run `alembic check`;
3. run database tests;
4. ensure `Base.metadata` registration tests reflect the new schema.

## Migration Rules

Never rewrite an already-pushed migration unless explicitly performing a
repository-history repair.

New schema evolution gets a new migration.

Migration upgrade and downgrade paths must remain coherent.

Use explicit constraints for important numeric ranges and foreign-key
relationships.

## Typing and Style

Use Python 3.13 typing.

Mypy runs in strict mode.

Prefer:

- precise return types;
- immutable dataclasses for value objects/results;
- enums for closed semantic sets;
- protocols for ports;
- dependency injection at application boundaries;
- small deterministic methods;
- docstrings on public classes/functions;
- comments for non-obvious domain decisions, not obvious syntax.

Avoid:

- `Any` unless serialization/dynamic boundaries genuinely require it;
- hidden global state;
- infrastructure imports from domain;
- magic business constants without semantic names;
- broad exception swallowing.

## Determinism

Given the same snapshot, policy, ruleset, algorithm version, and reference time,
results should be reproducible.

Sort unordered outputs before returning them where ordering is externally
observable.

Version algorithms/rules when behavior changes materially.

Do not introduce random ordering.

UUID identity may be random; semantic outputs should not depend on UUID order
unless UUID is used only as a deterministic tie-breaker for already equivalent
records.

## Testing Expectations

Every behavior change needs focused tests at the closest layer.

Typical progression:

1. targeted tests for changed module;
2. adjacent regression tests;
3. full `pytest`;
4. `mypy`;
5. `ruff format --check .`;
6. `ruff check .`;
7. `alembic check` for persistence/schema work;
8. `python -m veyra`.

Useful commands:

```bat
pytest
mypy
ruff format --check .
ruff check .
alembic check
python -m veyra
```

For a migration:

```bat
alembic upgrade head
alembic check
```

Do not weaken tests to hide a real production bug.

If a schema intentionally changes, update schema expectation tests to reflect
the new intended state.

## Git Workflow

Primary development branch: `dev`.

Before editing an existing file, inspect the current branch version rather than
reconstructing it from memory.

Keep diffs narrow.

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

After pushing:

```bat
git rev-parse HEAD
git status
git log -1 --oneline
```

Do not commit unrelated generated files, local databases, logs, or accidental
shell-redirection artifacts.

Windows CRLF warnings from Git are not failures by themselves.

## Change Discipline

Prefer adding one coherent capability per checkpoint.

Do not mix unrelated refactors into feature commits.

Do not reformat large unrelated files.

When changing an existing large file, make the smallest semantic change needed.

Keep backward compatibility unless the phase explicitly changes a contract.

## Current Scoring Architecture

The intended scoring flow is:

`ProfileAnalysisResult + AnalysisScoringPolicy`
`-> AnalysisScoringFeatureAdapter`
`-> tuple[ScoringFeature, ...]`
`-> WeightedScoringEngine`
`-> ScoreResult`
`-> SearchCandidate score + ScoreSnapshot audit record`

Application scoring rules currently support:

- fact-value criteria;
- hypothesis-value criteria;
- explicit education/institution relation criteria.

Do not invent universal product weights. Weights belong to configured scoring
policy.

## Definition of Done for New Intelligence Features

A permitted new intelligence feature is not complete merely because an
extractor exists.

When applicable, it should have a clear path:

`evidence`
`-> fact / signal / hypothesis`
`-> scoring adapter/policy support`
`-> score contribution`
`-> explanation / audit`

Also include:

- unit tests;
- application integration tests where relevant;
- deterministic behavior;
- source provenance;
- confidence semantics;
- scoring behavior if the feature is permitted for scoring.

## Agent Behavior

Before making substantial changes:

1. inspect the current implementation;
2. identify the owning layer;
3. preserve existing semantic boundaries;
4. write or update focused tests;
5. run the appropriate gate;
6. inspect the diff before committing.

If a requested change conflicts with these architectural rules, prefer the
architecture and explain the tradeoff rather than silently introducing debt.

Do not claim a gate is green unless the command was actually run and passed.
