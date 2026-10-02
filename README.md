# Agent Skill Factory

<p align="right">
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a>
</p>

[![CI](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.8.0-1769aa.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](ROADMAP.md)

Agent Skill Factory is an open-source local toolchain for generating, validating, evaluating, registering, and exporting reusable Agent Skills.

It turns real task briefs, documentation, codebase conventions, tool descriptions, and Agent traces into testable Skill packages instead of one long prompt.

```text
sources and traces -> reviewable plan -> Skill package -> lint/eval -> repair -> registry -> export
```

**Local-first. Reviewable plans. One small runtime dependency: PyYAML.** LLM access is optional: use local Ollama, an OpenAI-compatible API, or the deterministic offline workflow. `plan` + `generate --from-plan` separates review from writing; `generate --llm` writes directly and needs post-generation review.

## Project Status

Current version: `0.8.0`

The project is still alpha, but the local lifecycle is now usable end to end.
The following states describe local implementation, not field-validated Agent quality:

| Area | Status | Notes |
|---|---|---|
| Local CLI | Done | `init`, `ingest`, `plan`, `generate`, `lint`, `eval-generate`, `eval`, `repair`, provider health, registry/export/install, and schema commands. |
| Skill package writer | Integration verified | Writes concrete workflow/check/resource plans, marks incomplete workflows as drafts, and generates Codex interface metadata. |
| LLM planning | Done | Supports local Ollama and OpenAI-compatible APIs for structured `SkillPlan` generation. |
| Source/trace ingestion | Done | Deterministic plans from UTF-8 files, directories, and successful or failed Agent traces. |
| Static linter | Implemented | Safe YAML, standard optional fields, typed metadata, English/Chinese cues and configurable policies. |
| Eval runner | In progress | Source-aware drafts, trigger/task/runner evals, reports, and regression comparison. |
| Local registry/export | Done | File-based registry, source hashes, risk summary, eval status, and client directory export. |
| Runner abstraction | Done | Dry-run, optional LLM, and JSON subprocess Agent runners. |
| Repair loop | Done | Bounded repair plans, safe deterministic edits, lint/eval reruns, and rollback on regression. |
| Agent-backed evals | In progress | Generic subprocess adapter is available; first-party adapters and automatic trace capture remain. |

The suite covers the local lifecycle, YAML compatibility, reviewed plans and executable examples. CI tests Python 3.10-3.12 on Linux/Windows and separately builds and installs both source archives and wheels. See [v0.8 verification](docs/releases/v0.8.0.md) for results and limits.

v0.8 focuses on useful content and format compatibility. [v0.9](ROADMAP.md#v09-real-agent-evidence) will establish real Agent task evidence; v0.10 will harden distribution. [Three practical examples](examples/README.md) target Python coursework and experimental data/report workflows.

**Evaluation boundary:** keyword/package tests and dry-run scores do not prove Agent improvement. No first-party Agent adapter, sandbox or held-out generation benchmark is claimed.

## Scope and Boundaries

Agent Skill Factory is the small, headless core for the Skill lifecycle. It is designed to be used directly through the CLI or embedded behind a future desktop, web, course, or lab workspace.

Included today:

- deterministic and LLM-assisted `SkillPlan` creation
- source and Agent trace ingestion with provenance
- Skill package generation, linting, evaluation, and bounded repair
- configurable lint policies and source-aware eval draft generation
- local registry metadata, export, and installation
- local Ollama and OpenAI-compatible model providers
- an explicit subprocess protocol for external Agent eval runners

Not implemented yet:

- a graphical interface or hosted service
- first-party Agent adapters, runtime isolation, and automatic trace capture
- multi-user workspaces, review workflows, or cloud synchronization
- package signing, capability permissions, or a public marketplace

These boundaries are intentional. Hosted collaboration should build on the same tested core instead of duplicating its validation and security rules.

## Why

Agent Skills are a practical way to extend coding agents and workflow agents with domain-specific procedures, references, scripts, tools, and templates. A production-quality Skill should be scoped, concise, testable, and safe by default. A one-shot generated `SKILL.md` is not enough.

Agent Skill Factory focuses on the full local lifecycle:

```text
source material -> ingest/plan -> review -> generate -> lint -> eval -> registry -> export/install
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

Install from source:

```bash
python -m pip install -e .
skill-factory init .
skill-factory generate \
  --name "Release Note Builder" \
  --description "Use this skill when the agent needs to create release notes from repository changes." \
  --brief "Create concise release notes grounded in repository changes." \
  --step "Collect reviewed changes and retain their source identifiers." \
  --step "Group user-visible changes and note breaking changes separately." \
  --check "Every release item is supported by a reviewed source change." \
  --output skills
skill-factory lint skills/release-note-builder
```

This creates a package from explicit steps, then checks it locally. `--resources` creates directories only; complete resource content belongs in a reviewed plan. Generation never runs scripts.

Start with a complete reviewed example:

```bash
skill-factory generate --from-plan examples/plans/python-code-review.json --output skills
skill-factory lint skills/python-code-review --policy strict
python examples/skills/experiment-csv-check/scripts/check_csv.py examples/skills/experiment-csv-check/assets/sample.csv --required id --numeric value --unique id
```

Examples are included in the repository/source archive, not the runtime wheel. Download wheel/source artifacts from [GitHub releases](https://github.com/MuzeAnisichael/agent-skill-factory/releases); no PyPI publication is claimed.

Create a reviewable plan from local documents, code, and Agent traces, then generate from it:

```bash
skill-factory ingest docs src/example.py \
  --trace traces/release.trace.json \
  --name "Release Note Builder" \
  --output skill-plan.json
```

Review the plan and add task-specific `workflow` and `quality_checks`, then:

```bash
skill-factory generate --from-plan skill-plan.json --output skills
skill-factory eval-generate \
  --from-plan skill-plan.json \
  --output skills/release-note-builder/evals/evals.json
skill-factory lint skills/release-note-builder
```

Run local evals after adding `evals/evals.json`:

```bash
skill-factory eval skills/release-note-builder
skill-factory eval skills/release-note-builder --json
skill-factory eval skills/release-note-builder --markdown-output eval-report.md
skill-factory eval skills/release-note-builder --baseline-skill old-skills/release-note-builder
skill-factory eval-schema --output docs/eval-schema.json
```

Apply a stricter built-in lint policy or a versioned team policy:

```bash
skill-factory lint skills/release-note-builder --policy strict
skill-factory lint skills/release-note-builder --policy-file policies/team.json
```

Run runner-backed evals with the deterministic dry-run runner, or explicitly use an LLM runner:

```bash
skill-factory eval skills/release-note-builder --runner dry-run
skill-factory eval skills/release-note-builder \
  --runner llm \
  --provider ollama \
  --model llama3.1
skill-factory eval skills/release-note-builder \
  --runner subprocess \
  --runner-command '["python","adapters/my_agent.py"]'
```

Plan and apply bounded repairs:

```bash
skill-factory repair plan skills/release-note-builder
skill-factory repair plan skills/release-note-builder --json
skill-factory repair apply skills/release-note-builder
```

Repair can fix weak descriptions, missing referenced resources, oversized `SKILL.md` bodies, and missing positive eval assertions. Security-related findings are marked for manual review and are not auto-applied.

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
skill-factory provider-health --provider ollama --model llama3.1

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

To run from source without installing this package, first install `PyYAML>=6.0.2,<7`. On macOS or Linux:

```bash
PYTHONPATH=src python -m skill_factory --version
PYTHONPATH=src python -m skill_factory lint skills/release-note-builder
PYTHONPATH=src python -m skill_factory registry list
```

From source in PowerShell (PyYAML must already be installed):

```powershell
$env:PYTHONPATH = "src"
python -m skill_factory --version
python -m skill_factory lint skills/release-note-builder
python -m skill_factory registry list
```

Run tests from a source checkout:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Repository Layout

```text
src/skill_factory/       Core CLI, ingestion, planning, generation, lint/eval/repair, registry, schemas, and LLM providers
tests/                   Unit tests and offline fixtures for the local lifecycle
examples/                Three maintained Skills and a reviewed generation plan
tools/check_package.py   Clean source/wheel installation and CLI lifecycle check
docs/                    Architecture, ingestion, providers, evaluation, registry, security, and format docs
.github/                 CI, issue templates, and PR template
docs/README.md           Documentation index organized by workflow
ROADMAP.md               Development plan and completion table
```

## Documentation

- [Documentation Index](docs/README.md)
- [Roadmap and Completion Table](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [Development Plan](docs/development-plan.md)
- [Source and Trace Ingestion](docs/ingestion.md)
- [Skill Output Format](docs/skill-output-format.md)
- [Practical Examples](examples/README.md)
- [v0.8 Verification and Migration](docs/releases/v0.8.0.md)
- [LLM Providers](docs/llm-providers.md)
- [Lint Policies](docs/lint-policies.md)
- [Evaluation Strategy](docs/evaluation.md)
- [Runner Adapters](docs/runner-adapters.md)
- [Repair Loop](docs/repair.md)
- [Eval JSON Schema](docs/eval-schema.json)
- [Trace JSON Schema](docs/trace-schema.json)
- [Registry and Export](docs/registry.md)
- [Security Model](docs/security-model.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

## Contributing and Support

Contributions should keep the core small, deterministic where possible, and reviewable before file or tool actions. Start with [CONTRIBUTING.md](CONTRIBUTING.md), check the [roadmap](ROADMAP.md), and use the repository issue templates for reproducible bugs or scoped feature proposals.

For usage questions, see [SUPPORT.md](SUPPORT.md). Report vulnerabilities privately through the process in [SECURITY.md](SECURITY.md).

## Security

Generated Skills can influence agent behavior and tool use. Review all generated/imported instructions and code before use. Lint and eval are partial checks, not a trust guarantee or sandbox. See [SECURITY.md](SECURITY.md) and [Security Model](docs/security-model.md).

## License

MIT
