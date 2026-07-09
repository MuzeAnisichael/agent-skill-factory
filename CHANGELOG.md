# Changelog

All notable changes to this project will be documented in this file.

The project follows a simple pre-release changelog until versioned releases begin.

## Unreleased

### Added

- `v0.5.0` bounded repair loop.
- `skill-factory repair plan` for reviewable repair plans.
- `skill-factory repair apply` for safe deterministic edits with lint/eval reruns.
- Automatic repairs for weak descriptions, missing resources, oversized bodies, and missing positive eval assertions.
- Rollback on lint/eval regression and manual review blocks for security findings.
- `v0.4.0` runner-backed eval lifecycle.
- `runner_tests` eval file section for with-skill vs without-skill comparisons.
- Deterministic dry-run eval runner for network-free CI.
- Optional LLM eval runner using Ollama or OpenAI-compatible providers.
- `skill-factory eval --runner`, `--markdown`, `--markdown-output`, and `--baseline-skill`.
- Markdown eval reports and baseline Skill regression comparison.
- `v0.3.0` local registry and export lifecycle.
- `skill-factory registry add/list/show` for file-based Skill metadata.
- `skill-factory export` for direct package export to Agent client directories.
- `skill-factory install` for registry-based local installation.
- Source package SHA-256 and per-file hashes in registry entries.
- Lint-derived risk summaries and optional eval summaries in registry entries.
- `skill-factory eval-schema` and published `docs/eval-schema.json`.
- Registry/export documentation and updated v0.3 roadmap.
- Initial local CLI with `init`, `generate`, and `lint`.
- LLM planning via `skill-factory plan`.
- `generate --llm` mode for creating a structured `SkillPlan` before deterministic file generation.
- Local Ollama provider using `/api/chat`.
- OpenAI-compatible API provider using `/v1/chat/completions`.
- LLM provider documentation.
- Bilingual README support with English and Simplified Chinese entry points.
- Initial `skill-factory eval` command with local trigger evals, task assertions, JSON reports, and fixture tests.
- Strict eval configuration validation with clearer schema errors.
- Skill package writer for `SKILL.md`, optional resource directories, and `agents/openai.yaml`.
- Static linter for Skill metadata, naming, resource references, unsafe instructions, and Python script syntax.
- Unit tests for CLI, generation, linting, and naming.
- Roadmap, completion table, security model, contribution guide, and CI workflow.
