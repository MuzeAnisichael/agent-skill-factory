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

Status: local eval implementation is complete for trigger cases, task assertions, strict configuration validation, JSON reports, and published JSON Schema. Baseline Agent-backed evals remain planned.

## Milestone 4: Repair Loop

Deliverables:

- Bounded edit generation.
- Eval-aware acceptance rule.
- Version snapshots.
- Regression checks.

Exit criteria:

- The system can improve a weak Skill description or split an oversized Skill into references without manual rewrite.

## Milestone 5: Registry and Export

Deliverables:

- Local registry index.
- Version metadata.
- Risk metadata.
- Export to `.agents/skills/`.
- Export adapters for `.claude/skills/` and Codex-style user skills.

Exit criteria:

- Users can generate, validate, version, and install a Skill locally.

Status: local registry and export/install implementation complete in `v0.3.0`. Hosted registry, signing, dependency policy, and trust-policy checks remain future work.

## Implementation Bias

Start with Python for the CLI and validation tooling. Keep the core package small, file-based, and testable. Avoid introducing a database until the registry needs concurrent users or hosted collaboration.

## First Technical Tasks

1. Define internal data models for Skill plans and lint results.
2. Implement Skill package writer.
3. Implement static linter.
4. Add fixture Skills for valid, invalid, risky, and oversized examples.
5. Add unit tests for validation rules.

## Completion Matrix

| Workstream | Current State | Completion |
|---|---|---:|
| Repository presentation | README, license, security, contributing, support, changelog, CI, templates | 100% |
| CLI foundation | `init`, `plan`, `generate`, `lint`, `eval`, `eval-schema`, `registry`, `export`, `install` | 100% |
| LLM planning | Ollama and OpenAI-compatible structured `SkillPlan` generation | 100% |
| Skill generation | Standard folder output with optional resources | 80% |
| Static linting | Core checks implemented | 70% |
| Evaluation | Local trigger evals, task assertions, config validation, JSON Schema, JSON reports, fixture tests | 60% |
| Repair loop | Design documented | 0% |
| Registry/export | Local registry, source hashes, risk/eval metadata, export and install commands | 100% |
