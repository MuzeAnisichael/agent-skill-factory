# Agent Skill Factory

<p align="right">
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a>
</p>

[![CI](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](ROADMAP.md)

Agent Skill Factory is an open-source local toolchain for generating, validating, evaluating, registering, and exporting reusable Agent Skills.

It turns real task briefs, documentation, codebase conventions, tool descriptions, and future agent traces into testable Skill packages instead of one long prompt.

## Project Status

Current version: `0.3.0`

The project is still alpha, but the local lifecycle is now usable end to end:

| Area | Status | Notes |
|---|---|---|
| Local CLI | Done | `init`, `plan`, `generate`, `lint`, `eval`, `registry`, `export`, `install`, and `eval-schema`. |
| Skill package writer | Done | Generates `SKILL.md`, optional resources, and `agents/openai.yaml`. |
| LLM planning | Done | Supports local Ollama and OpenAI-compatible APIs for structured `SkillPlan` generation. |
| Static linter | In progress | Covers naming, frontmatter, missing resources, risky instructions, and Python syntax. |
| Eval runner | In progress | Local trigger evals, task assertions, strict schema validation, and JSON reports. |
| Local registry/export | Done | File-based registry, source hashes, risk summary, eval status, and client directory export. |
| Repair loop | Planned | Bounded fixes based on lint and eval failures. |
| Agent-backed evals | Planned | Runtime comparison with and without Skills. |

## Why

Agent Skills are a practical way to extend coding agents and workflow agents with domain-specific procedures, references, scripts, tools, and templates. A production-quality Skill should be scoped, concise, testable, and safe by default. A one-shot generated `SKILL.md` is not enough.

Agent Skill Factory focuses on the full local lifecycle:

```text
source material -> skill planning -> skill generation -> lint -> eval -> registry -> export/install
```

## Skill Package Target

```text
skill-name/
|-- SKILL.md
|-- references/
|-- scripts/
|-- assets/
`-- agents/openai.yaml
```

`SKILL.md` should contain only high-value instructions. Long domain material goes into `references/`, deterministic operations go into `scripts/`, and reusable templates or static files go into `assets/`.

## Quick Start

Requirements:

- Python 3.10+
- Git

Run from source:

```bash
python -m pip install -e .
skill-factory init .
skill-factory generate \
  --name "Release Note Builder" \
  --description "Use this skill when the agent needs to create release notes from repository changes." \
  --brief "Create concise release notes grounded in repository changes." \
  --resources references,scripts \
  --output skills
skill-factory lint skills/release-note-builder
```

Run local evals after adding `evals/evals.json`:

```bash
skill-factory eval skills/release-note-builder
skill-factory eval skills/release-note-builder --json
skill-factory eval-schema --output docs/eval-schema.json
```

Register and install a Skill locally:

```bash
skill-factory registry add skills/release-note-builder --version 0.1.0
skill-factory registry list
skill-factory install release-note-builder --target agent-skills
```

Export directly without a registry:

```bash
skill-factory export skills/release-note-builder --target codex --output .codex/skills
skill-factory export skills/release-note-builder --target claude-code --output .claude/skills
```

Use a local Ollama model to plan and generate:

```bash
skill-factory plan \
  --provider ollama \
  --model llama3.1 \
  --brief "Create a Skill for turning merged pull requests into release notes."

skill-factory generate \
  --llm \
  --provider ollama \
  --model llama3.1 \
  --brief "Create a Skill for turning merged pull requests into release notes." \
  --resources references,scripts \
  --output skills
```

Use an OpenAI-compatible API:

```bash
skill-factory plan \
  --provider openai-compatible \
  --api-base https://api.openai.com/v1 \
  --api-key "$OPENAI_API_KEY" \
  --model "$OPENAI_MODEL" \
  --brief "Create a Skill for reviewing Terraform changes."
```

Without installation:

```bash
PYTHONPATH=src python -m skill_factory --version
PYTHONPATH=src python -m skill_factory lint skills/release-note-builder
PYTHONPATH=src python -m skill_factory registry list
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Repository Layout

```text
src/skill_factory/       Core CLI, generator, linter, evaluator, registry, schemas, and LLM providers
tests/                   Unit tests for CLI, planning, generation, linting, evals, registry, and schemas
docs/                    Architecture, LLM providers, evaluation, registry, security, and format docs
.github/                 CI, issue templates, and PR template
ROADMAP.md               Development plan and completion table
```

## Documentation

- [Roadmap and Completion Table](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [Development Plan](docs/development-plan.md)
- [Skill Output Format](docs/skill-output-format.md)
- [LLM Providers](docs/llm-providers.md)
- [Evaluation Strategy](docs/evaluation.md)
- [Eval JSON Schema](docs/eval-schema.json)
- [Registry and Export](docs/registry.md)
- [Security Model](docs/security-model.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

## Security

Generated Skills can influence agent behavior and tool use. Treat all generated or imported Skills as untrusted until they pass lint and eval. See [SECURITY.md](SECURITY.md) and [Security Model](docs/security-model.md).

## License

MIT
