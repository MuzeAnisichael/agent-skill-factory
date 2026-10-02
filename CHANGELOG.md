# Changelog

All notable changes to this project will be documented in this file.

The project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions during its pre-release phase.

## Unreleased

## 0.8.0 - 2026-10-03

### Added

- Safe YAML parsing with duplicate-key diagnostics, standard optional metadata and typed limits.
- Chinese trigger cues and weighted advisory description length.
- Additive `workflow`, `quality_checks`, and complete `resource_files` plan fields, plus manual `--step`/`--check` options.
- Three maintained student/research examples: Python review, read-only experimental CSV checks, and report consistency review.
- Clean wheel/source-archive install checks and cross-platform packaging CI.
- Verification, migration and evidence-based release planning documentation.

### Changed

- PyYAML is the only runtime dependency; model access remains optional.
- Missing workflow steps now remain explicit drafts; resource directory selection no longer creates fake helpers or templates.
- Roadmap prioritizes v0.9 real Agent evidence and v0.10 reliable distribution before a platform pilot.
- Architecture and bilingual READMEs distinguish package checks from actual Agent effectiveness.

### Fixed

- Corrected quoted Codex UI metadata under `interface` with bounded blurbs and explicit Skill invocation.
- Enforced single internal hyphens and specification description/compatibility length limits.
- Preserved optional metadata during YAML-aware description repair and blocked edits/evals on invalid YAML.
- Rejected escaping resource paths, symlink writes, case-insensitive duplicate and file/directory collisions before generation.

### Migration

- Existing schema-version-1 plans remain supported with empty defaults for new fields.
- Review concrete steps and remove old scaffold resources manually before strict lint or publication.
- See [v0.8 verification and migration](docs/releases/v0.8.0.md); no PyPI publication or real Agent benchmark is claimed.

## 0.7.0 - 2026-08-23

### Added

- Built-in `standard`, `strict`, and `permissive` lint policies plus versioned custom JSON policies.
- `skill-factory eval-generate` for deterministic eval drafts from SkillPlan examples, failed tasks, constraints, and briefs.
- `skill-factory provider-health` for Ollama and OpenAI-compatible endpoint and model discovery checks.
- A subprocess Agent eval runner with a JSON stdin/stdout contract, explicit argument arrays, timeouts, and response validation.
- Offline tests and documentation for policy, eval generation, provider health, and runner adapter behavior.

### Changed

- Reorganized the bilingual README around project scope, workflows, current limitations, and contributor entry points.
- Added a documentation index, repository-wide text settings, cross-platform CI, and dependency update configuration.
- Converted runner failures into structured failed eval cases instead of uncaught provider or process errors.

### Fixed

- Made the registry export test robust to equivalent Windows short and long path aliases.

## 0.6.0 - 2026-07-10

### Added

- `skill-factory ingest` for files, directories, and successful or failed trace runs.
- Versioned `SkillPlan` JSON with constraints, terminology, tool candidates, failure cases, source hashes, and review notes.
- `generate --from-plan` for review-before-write workflows.
- Source-backed `references/sources.md` generation without copying indexed documents.
- Published Trace JSON Schema and `skill-factory trace-schema`.
- Shared prompt-injection and dangerous-instruction filtering for ingestion, lint, and repair.

## 0.5.0 - 2026-07-09

### Added

- `skill-factory repair plan` for reviewable repair plans.
- `skill-factory repair apply` for safe deterministic edits with lint/eval reruns.
- Automatic repairs for weak descriptions, missing resources, oversized bodies, and missing positive eval assertions.
- Rollback on lint/eval regression and manual review blocks for security findings.

## 0.4.0 - 2026-07-09

### Added

- `runner_tests` eval file section for with-skill vs without-skill comparisons.
- Deterministic dry-run eval runner for network-free CI.
- Optional LLM eval runner using Ollama or OpenAI-compatible providers.
- `skill-factory eval --runner`, `--markdown`, `--markdown-output`, and `--baseline-skill`.
- Markdown eval reports and baseline Skill regression comparison.

## 0.3.0 - 2026-07-08

### Added

- `skill-factory registry add/list/show` for file-based Skill metadata.
- `skill-factory export` for direct package export to Agent client directories.
- `skill-factory install` for registry-based local installation.
- Source package SHA-256 and per-file hashes in registry entries.
- Lint-derived risk summaries and optional eval summaries in registry entries.
- `skill-factory eval-schema` and published `docs/eval-schema.json`.

## 0.2.0 - 2026-07-08

### Added

- LLM planning via `skill-factory plan`.
- `generate --llm` mode for creating a structured `SkillPlan` before deterministic file generation.
- Local Ollama provider using `/api/chat`.
- OpenAI-compatible API provider using `/v1/chat/completions`.
- Bilingual README support with English and Simplified Chinese entry points.
- Local trigger and task evals with JSON reports and schema validation.
- Strict eval configuration validation with clearer schema errors.

## 0.1.0 - 2026-07-07

### Added

- Initial local CLI with `init`, `generate`, and `lint`.
- Skill package writer for `SKILL.md`, optional resource directories, and `agents/openai.yaml`.
- Static linter for Skill metadata, naming, resource references, unsafe instructions, and Python script syntax.
- Unit tests for CLI, generation, linting, and naming.
- Roadmap, completion table, security model, contribution guide, and CI workflow.
