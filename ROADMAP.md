# Roadmap and Completion Table

Agent Skill Factory is developed in small, testable milestones. The near-term goal is a reliable local CLI before any hosted service or marketplace work.

Current version target completed in this repository: `v0.4.0`.

## Completion Summary

| Milestone | Status | Completion | Evidence | Next Step |
|---|---:|---:|---|---|
| M0 Repository and spec | Done | 100% | README, docs, MIT license, security model | Keep docs aligned with implementation |
| M1 Local CLI skeleton | Done | 100% | `skill-factory init`, `generate`, `lint` | Improve CLI ergonomics |
| M1.5 LLM planning | Done | 100% | `plan`, `generate --llm`, Ollama and OpenAI-compatible clients | Add provider health checks and richer errors |
| M2 Static linter | In progress | 70% | Naming, frontmatter, resource, risk, syntax checks | Add policy profiles and broader unsafe-pattern coverage |
| M3 Local eval runner | In progress | 75% | `eval`, trigger evals, task assertions, runner tests, strict schema validation, JSON Schema, Markdown reports | Add model-graded and trace-backed evals |
| M3.5 Local registry and export | Done | 100% | `registry add/list/show`, `export`, `install`, source hashes, risk and eval metadata | Add signing and trust policies later |
| M3.8 Runner-backed evals | Done | 100% | Dry-run runner, optional LLM runner, with/without Skill comparison, baseline Skill comparison | Integrate real Agent runtimes later |
| M4 Repair loop | Planned | 0% | Architecture documented | Add bounded repair plan format |
| M5 Source and trace ingestion | Planned | 0% | Architecture documented | Convert docs/code/traces into structured Skill inputs |
| M6 Hosted/web surface | Later | 0% | Out of initial scope | Revisit after CLI is useful |

## v0.4.0 Scope

Goal: make evals measure task execution behavior, not only package text.

Completed:

- Add a runner abstraction for task execution.
- Add a local dry-run runner for deterministic tests.
- Add optional LLM runner integration using existing Ollama and OpenAI-compatible clients.
- Compare without-skill vs with-skill outputs.
- Emit Markdown eval reports for review.
- Add regression gates for old Skill vs new Skill.
- Extend `evals/evals.json` with `runner_tests`.
- Update published `docs/eval-schema.json`.
- Add CLI flags: `--runner`, `--markdown`, `--markdown-output`, and `--baseline-skill`.
- Add unit tests for runner behavior, CLI reporting, schema stability, and regression comparison.

Acceptance criteria:

- A sample Skill can show measurable improvement over baseline. Done.
- Failed evals produce actionable diagnostics. Done.
- Eval fixtures run in CI without external network requirements. Done.
- Optional model-backed evals are skipped unless explicitly configured. Done.

Not included in v0.4:

- Real Agent runtime control.
- Tool-call trace evaluation.
- Model-graded qualitative scoring.
- Cost and latency tracking.

## v0.5 Development Plan

Goal: make generated Skills iteratively better without rewriting them blindly.

Planned work:

- Convert lint and eval failures into bounded edit plans.
- Apply small changes to `SKILL.md` or resource files.
- Re-run lint and eval after each repair.
- Accept a repair only if held-out quality is preserved or improved.

Acceptance criteria:

- The system can improve a weak description.
- The system can split oversized body content into `references/`.
- The system refuses changes that increase risk without approval.

## Detailed Completion Table

| Component | Done | Remaining |
|---|---|---|
| CLI command structure | `init`, `plan`, `generate`, `lint`, `eval`, `eval-schema`, `registry`, `export`, `install` | `repair`, ingestion commands |
| Eval command | Default `evals/evals.json`, `--json`, `--markdown`, `--markdown-output`, `--eval-file`, `--no-lint`, `--runner`, `--baseline-skill` | Real Agent runtime adapters |
| Eval validation | Internal validation plus published `docs/eval-schema.json` for trigger, task, and runner tests | Editor examples and schema-version migration policy |
| LLM provider layer | Ollama and OpenAI-compatible providers | Provider health checks, streaming, richer errors |
| Skill planning | LLM-generated structured `SkillPlan` | Plan validation, source attribution, confidence reporting |
| Skill writer | `SKILL.md`, `agents/openai.yaml`, optional resource dirs | Better templates, source attribution, deterministic plan files |
| Naming rules | Hyphen-case normalization and validation | Configurable naming policies |
| Frontmatter parser | Minimal YAML-like parsing for simple metadata | More robust diagnostics and line numbers |
| Linter | Description, folder match, body length, missing resources, dangerous patterns | Policy profiles, more unsafe patterns, duplicate-content checks |
| Runner layer | Dry-run runner and optional LLM runner | Real Agent runtime adapters, trace collection, cost metrics |
| Local registry | JSON registry, source hashes, risk/eval metadata | Signing, trust policy, dependency metadata |
| Export/install | Direct export and registry-based install to local client directories | Packaged archives and hosted registry adapters |
| Tests | Unit tests for CLI, generation, linter, naming, LLM planning, local eval, runner, registry, schema | Fixture matrix and CI coverage expansion |
| Documentation | Architecture, format, eval, registry, security, roadmap, bilingual README | Contributor walkthroughs and more examples |
| CI | Workflow file added | Add lint/type checks when tool choices stabilize |

## Prioritized Backlog

1. Add repair-loop prototype.
2. Add lint policy profiles.
3. Add source/document ingestion into structured Skill inputs.
4. Add real Agent runtime adapter for evals.
5. Add model-graded evals, cost, latency, and tool-call metrics.
6. Add signed export packages and registry trust policy.
