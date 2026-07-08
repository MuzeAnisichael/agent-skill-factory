# Agent Skill Factory

[![CI](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](ROADMAP.md)

Agent Skill Factory is an open-source toolchain for generating, validating, and publishing reusable Agent Skills.

目标：把真实任务、文档、代码库、工具说明和 Agent 运行 trace 转化为可复用、可评测、可发布的 Skill 包，而不是只生成一段长 prompt。

## Project Status

This project is in early alpha. The first working slice is a local Python CLI that can initialize a workspace, generate a draft Skill package, and lint Skill quality and safety.

| Area | Status | Notes |
|---|---|---|
| Local CLI | Done | `init`, `generate`, and `lint` are implemented. |
| Skill package writer | Done | Generates `SKILL.md`, optional resources, and `agents/openai.yaml`. |
| LLM planning | Done | Supports local Ollama and OpenAI-compatible APIs for structured SkillPlan generation. |
| Static linter | In progress | Initial checks cover naming, frontmatter, missing resources, risky instructions, and Python script syntax. |
| Eval runner | Planned | Trigger and with-skill vs without-skill evals are next. |
| Repair loop | Planned | Bounded auto-fixes based on lint and eval failures. |
| Registry and export | Planned | Local registry, version metadata, and install adapters. |

## Why

Agent Skills are becoming a practical way to extend coding agents and workflow agents with domain-specific procedures, tools, references, scripts, and templates. A good Skill should be concise, scoped, testable, and safe. A one-shot LLM-generated `SKILL.md` is not enough for production use.

Agent Skill Factory focuses on the full lifecycle:

```text
source material -> skill planning -> skill generation -> lint -> eval -> repair -> registry -> publish
```

## Scope

This repository starts with a lightweight but complete architecture for:

- Generating standard Skill packages.
- Validating `SKILL.md` structure and triggering quality.
- Comparing with-skill vs without-skill task performance.
- Detecting safety and permission risks.
- Managing versions in a local or hosted Skill Registry.
- Exporting to Agent Skills-compatible clients such as Codex, Claude Code, and ADK-style runtimes.

## Skill Package Target

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
├── assets/
└── agents/openai.yaml
```

`SKILL.md` should contain only high-value instructions. Long domain material goes into `references/`, deterministic operations go into `scripts/`, and reusable templates or static files go into `assets/`.

## MVP Modules

1. Builder: create a draft Skill from task examples and source materials.
2. Linter: check naming, metadata, length, missing files, vague instructions, and unsafe permissions.
3. Eval Runner: run trigger tests and with-skill vs without-skill task comparisons.
4. Repair Agent: make bounded edits based on lint and eval failures.
5. Registry: store Skill versions, scores, dependencies, risk level, and export targets.

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
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Repository Layout

```text
src/skill_factory/       Core CLI, generator, linter, and data models
tests/                   Unit tests for CLI, generation, and linting
docs/                    Architecture, evaluation, security, and format docs
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
- [Security Model](docs/security-model.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

## Current CLI

```bash
skill-factory --help
skill-factory init ./workspace
skill-factory plan --provider ollama --model llama3.1 --brief "Create a Skill for release notes."
skill-factory generate --name "Release Note Builder" --brief "Create release notes." --output skills
skill-factory generate --llm --provider ollama --model llama3.1 --brief "Create release notes." --output skills
skill-factory lint skills/release-note-builder
```

The generated Skill target is intentionally simple and compatible with Agent Skills-style clients:

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
├── assets/
└── agents/openai.yaml
```

## Contributing

Contributions are welcome in small, reviewable changes. Good first areas include lint rules, fixture Skills, eval file formats, CLI ergonomics, and documentation examples. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Generated Skills can influence agent behavior and tool use. Treat all generated Skills as untrusted until linted and evaluated. See [SECURITY.md](SECURITY.md) and [Security Model](docs/security-model.md).

## License

MIT
