# Agent Skill Factory

Agent Skill Factory is an open-source project for generating, validating, and publishing reusable Agent Skills.

目标：把真实任务、文档、代码库、工具说明和 Agent 运行 trace 转化为可复用、可评测、可发布的 Skill 包，而不是只生成一段长 prompt。

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

Without installation:

```bash
PYTHONPATH=src python -m skill_factory --version
PYTHONPATH=src python -m skill_factory lint skills/release-note-builder
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Documentation

- [Architecture](docs/architecture.md)
- [Development Plan](docs/development-plan.md)
- [Skill Output Format](docs/skill-output-format.md)
- [Evaluation Strategy](docs/evaluation.md)
- [Security Model](docs/security-model.md)

## Status

Early development. The repository includes an initial local CLI for workspace initialization, draft Skill generation, and static linting.

## License

MIT
