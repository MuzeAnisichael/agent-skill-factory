# Development Plan

For a concise public-facing milestone table, see [Roadmap and Completion Table](../ROADMAP.md).

## Product Goal

Build a practical toolchain for creating Agent Skills that are:

- Reusable across compatible Agent clients.
- Grounded in real project or organization knowledge.
- Concise enough to preserve context.
- Evaluated against realistic tasks.
- Safe by default.

## Non-Goals

- Do not build a general Agent marketplace in the first version.
- Do not auto-install untrusted Skills into user environments.
- Do not support arbitrary remote code execution.
- Do not optimize for every Agent client-specific extension at the start.

## Milestone 0: Repository and Spec

Status: complete.

Deliverables:

- Public repository.
- MIT license.
- Architecture documentation.
- Output Skill format.
- Evaluation and security model.

Exit criteria:

- A contributor can understand what will be built and how to help.

## Milestone 1: Local CLI Skeleton

Deliverables:

- `skill-factory init`
- `skill-factory generate`
- `skill-factory lint`
- Local config file.
- Basic JSON schema for internal planning records.

Exit criteria:

- Given a small task brief, the CLI creates a valid Skill directory.

Status: initial implementation complete.

## Milestone 2: Static Linter

Deliverables:

- Name and frontmatter validation.
- Description quality checks.
- Reference existence checks.
- Length checks.
- Permission and shell-risk checks.
- JSON report output.

Exit criteria:

- Invalid or unsafe draft Skills fail lint with actionable messages.

Status: initial implementation complete for frontmatter, naming, resource references, length, generic filler, dangerous instruction, and Python syntax checks.

## Milestone 3: Eval Runner

Deliverables:

- `evals/evals.json` convention.
- Trigger test format.
- Task eval format.
- With-skill vs without-skill runner abstraction.
- Markdown and JSON reports.

Exit criteria:

- A Skill can prove improvement over a baseline on at least one small eval set.

Status: local eval implementation is complete for trigger cases, task assertions, runner-backed evals, strict configuration validation, JSON and Markdown reports, published JSON Schema, and baseline Skill comparison. Real Agent runtime adapters remain planned.

## Milestone 3.5: Registry and Export

Deliverables:

- Local registry index.
- Version metadata.
- Risk metadata.
- Export to `.agents/skills/`.
- Export adapters for `.claude/skills/` and Codex-style user skills.

Exit criteria:

- Users can generate, validate, version, and install a Skill locally.

Status: local registry and export/install implementation complete in `v0.3.0`. Hosted registry, signing, dependency policy, and trust-policy checks remain future work.

## Milestone 4: Repair Loop

Deliverables:

- Bounded edit generation.
- Eval-aware acceptance rule.
- Version snapshots.
- Regression checks.

Exit criteria:

- The system can improve a weak Skill description or split an oversized Skill into references without manual rewrite.

Status: initial implementation complete in `v0.5.0` with `repair plan`, `repair apply`, deterministic edits, lint/eval reruns, rollback on regression, and manual security blocks.

## Milestone 5: Source and Trace Ingestion

Deliverables:

- Recursive bounded ingestion for UTF-8 documents and code.
- Deterministic task, constraint, terminology, and summary extraction.
- Versioned successful/failed Agent trace format.
- Reviewable `SkillPlan` JSON with source hashes and safety review notes.
- Source-attributed generation through `generate --from-plan`.

Exit criteria:

- Users can create and review a source-grounded plan without model access, then generate a Skill
  that records provenance without copying the source documents.

Status: complete in `v0.6.0` with `ingest`, `generate --from-plan`, Trace schema validation,
prompt-injection filtering, source indexes, and offline fixtures.

## Implementation Bias

Start with Python for the CLI and validation tooling. Keep the core package small, file-based, and testable. Avoid introducing a database until the registry needs concurrent users or hosted collaboration.

## Next Technical Tasks

1. Add configurable lint policy profiles.
2. Generate draft eval cases from ingested examples and failure cases.
3. Add provider health checks and clearer connectivity diagnostics.
4. Implement the first real Agent runtime adapter and trace collector.
5. Add signed export packages and registry trust policies.

## Completion Matrix

| Workstream | Current State | Completion |
|---|---|---:|
| Repository presentation | README, license, security, contributing, support, changelog, CI, templates | 100% |
| CLI foundation | `init`, `ingest`, `plan`, `generate`, `lint`, `eval`, `repair`, schema commands, `registry`, `export`, `install` | 100% |
| LLM planning | Ollama and OpenAI-compatible structured `SkillPlan` generation | 100% |
| Skill generation | Standard folder output with optional resources and source attribution | 90% |
| Static linting | Core checks implemented | 75% |
| Evaluation | Local trigger evals, task assertions, runner tests, config validation, JSON Schema, JSON/Markdown reports, fixture tests | 75% |
| Runner layer | Dry-run runner and optional LLM runner | 100% |
| Repair loop | Bounded plan/apply flow, deterministic edits, rollback on regression, manual security blocks | 100% |
| Registry/export | Local registry, source hashes, risk/eval metadata, export and install commands | 100% |
| Source/trace ingestion | Bounded deterministic extraction, Trace validation, versioned plans, source hashes, review notes | 100% |
