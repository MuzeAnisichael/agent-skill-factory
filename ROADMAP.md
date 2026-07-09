# Roadmap and Completion Table

Agent Skill Factory is developed in small, testable milestones. The near-term goal is a reliable local CLI before any hosted service or marketplace work.

Current version target completed in this repository: `v0.5.0`.

## Completion Summary

| Milestone | Status | Completion | Evidence | Next Step |
|---|---:|---:|---|---|
| M0 Repository and spec | Done | 100% | README, docs, MIT license, security model | Keep docs aligned with implementation |
| M1 Local CLI skeleton | Done | 100% | `skill-factory init`, `generate`, `lint` | Improve CLI ergonomics |
| M1.5 LLM planning | Done | 100% | `plan`, `generate --llm`, Ollama and OpenAI-compatible clients | Add provider health checks and richer errors |
| M2 Static linter | In progress | 75% | Naming, frontmatter, resource, risk, syntax checks | Add policy profiles and broader unsafe-pattern coverage |
| M3 Local eval runner | In progress | 75% | `eval`, trigger evals, task assertions, runner tests, strict schema validation, JSON Schema, Markdown reports | Add model-graded and trace-backed evals |
| M3.5 Local registry and export | Done | 100% | `registry add/list/show`, `export`, `install`, source hashes, risk and eval metadata | Add signing and trust policies later |
| M3.8 Runner-backed evals | Done | 100% | Dry-run runner, optional LLM runner, with/without Skill comparison, baseline Skill comparison | Integrate real Agent runtimes later |
| M4 Repair loop | Done | 100% | `repair plan`, `repair apply`, bounded edits, rollback on regression | Add LLM-assisted repair proposals later |
| M5 Source and trace ingestion | Planned | 0% | Architecture documented | Convert docs/code/traces into structured Skill inputs |
| M6 Hosted/web surface | Later | 0% | Out of initial scope | Revisit after CLI is useful |

## v0.5.0 Scope

Goal: make generated Skills iteratively better without rewriting them blindly.

Completed:

- Convert lint and eval failures into a bounded repair plan.
- Add `skill-factory repair plan`.
- Add `skill-factory repair apply`.
- Apply deterministic edits to `SKILL.md` and missing resource files.
- Improve weak or missing descriptions.
- Create missing referenced resources.
- Split oversized `SKILL.md` body content into `references/overflow.md`.
- Add missing positive eval assertions as explicit repair notes.
- Re-run lint and eval after repair.
- Roll back when lint or eval quality regresses.
- Refuse security-related findings by default and mark them for manual review.

Acceptance criteria:

- The system can improve a weak description. Done.
- The system can split oversized body content into `references/`. Done.
- The system refuses changes that increase risk without approval. Done.
- Repair fixtures run in CI without external network requirements. Done.

Not included in v0.5:

- LLM-generated edit plans.
- Multi-file semantic refactors.
- Automatic removal of dangerous instructions.
- Real Agent runtime repair scoring.

## v0.6 Development Plan

Goal: convert richer source material into structured Skill inputs.

Planned work:

- Add source ingestion for text files and directories.
- Extract task examples, constraints, terminology, and source references.
- Generate deterministic `SkillPlan` inputs from source material.
- Add trace ingestion format for successful or failed Agent runs.
- Preserve source attribution in generated Skills.

Acceptance criteria:

- A user can point the CLI at docs or code snippets and get a reviewable SkillPlan.
- Generated Skills include source references without copying large source files into `SKILL.md`.
- Ingestion fixtures run in CI without model access.

## Detailed Completion Table

| Component | Done | Remaining |
|---|---|---|
| CLI command structure | `init`, `plan`, `generate`, `lint`, `eval`, `repair`, `eval-schema`, `registry`, `export`, `install` | ingestion commands |
| Eval command | Default `evals/evals.json`, `--json`, `--markdown`, `--markdown-output`, `--eval-file`, `--no-lint`, `--runner`, `--baseline-skill` | Real Agent runtime adapters |
| Eval validation | Internal validation plus published `docs/eval-schema.json` for trigger, task, and runner tests | Editor examples and schema-version migration policy |
| Repair loop | Repair planning, deterministic edits, rerun checks, rollback on regression, manual security blocks | LLM-assisted proposals and richer patch previews |
| LLM provider layer | Ollama and OpenAI-compatible providers | Provider health checks, streaming, richer errors |
| Skill planning | LLM-generated structured `SkillPlan` | Source attribution, confidence reporting |
| Skill writer | `SKILL.md`, `agents/openai.yaml`, optional resource dirs | Better templates, source attribution, deterministic plan files |
| Naming rules | Hyphen-case normalization and validation | Configurable naming policies |
| Frontmatter parser | Minimal YAML-like parsing for simple metadata | More robust diagnostics and line numbers |
| Linter | Description, folder match, body length, missing resources, dangerous patterns | Policy profiles, more unsafe patterns, duplicate-content checks |
| Runner layer | Dry-run runner and optional LLM runner | Real Agent runtime adapters, trace collection, cost metrics |
| Local registry | JSON registry, source hashes, risk/eval metadata | Signing, trust policy, dependency metadata |
| Export/install | Direct export and registry-based install to local client directories | Packaged archives and hosted registry adapters |
| Tests | Unit tests for CLI, generation, linter, naming, LLM planning, local eval, repair, runner, registry, schema | Fixture matrix and CI coverage expansion |
| Documentation | Architecture, format, eval, repair, registry, security, roadmap, bilingual README | Contributor walkthroughs and more examples |
| CI | Workflow file added | Add lint/type checks when tool choices stabilize |

## Prioritized Backlog

1. Add source/document ingestion into structured Skill inputs.
2. Add lint policy profiles.
3. Add real Agent runtime adapter for evals.
4. Add model-graded evals, cost, latency, and tool-call metrics.
5. Add LLM-assisted repair proposals behind the existing bounded repair gate.
6. Add signed export packages and registry trust policy.
