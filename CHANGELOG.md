# Changelog

All notable changes to this project will be documented in this file.

The project follows a simple pre-release changelog until versioned releases begin.

## Unreleased

### Added

- Initial local CLI with `init`, `generate`, and `lint`.
- LLM planning via `skill-factory plan`.
- `generate --llm` mode for creating a structured `SkillPlan` before deterministic file generation.
- Local Ollama provider using `/api/chat`.
- OpenAI-compatible API provider using `/v1/chat/completions`.
- LLM provider documentation.
- Bilingual README support with English and Simplified Chinese entry points.
- Initial `skill-factory eval` command with local trigger evals, task assertions, JSON reports, and fixture tests.
- Skill package writer for `SKILL.md`, optional resource directories, and `agents/openai.yaml`.
- Static linter for Skill metadata, naming, resource references, unsafe instructions, and Python script syntax.
- Unit tests for CLI, generation, linting, and naming.
- Roadmap, completion table, security model, contribution guide, and CI workflow.
