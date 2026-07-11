# Roadmap and Completion Table

Agent Skill Factory is developed in small, testable milestones. The near-term goal is a reliable local CLI before any hosted service or marketplace work.

Current version target completed in this repository: `v0.6.0`.

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
| M5 Source and trace ingestion | Done | 100% | `ingest`, Trace schema, versioned plans, source hashes, review notes | Broaden extractors from real usage |
| M6 Hosted/web surface | Later | 0% | Out of initial scope | Defer until policy and runtime gates mature |

## v0.6.0 Scope

Goal: convert richer source material into structured Skill inputs.

Completed:

- Added recursive UTF-8 text and code ingestion with bounded file and byte limits.
- Added deterministic extraction for task examples, constraints, terminology, and compact briefs.
- Added a versioned Trace format for successful and failed Agent runs.
- Added observed tool candidates and failure cases to `SkillPlan`.
- Added prompt-injection filtering with explicit review notes.
- Added `generate --from-plan` for review-before-write generation.
- Added `references/sources.md` with relative paths, source kinds, sizes, and SHA-256 hashes.
- Published `docs/trace-schema.json` and offline ingestion fixtures.

Acceptance criteria:

- A user can point the CLI at docs or code snippets and get a reviewable SkillPlan. Done.
- Generated Skills include source references without copying large source files into `SKILL.md`. Done.
- Ingestion fixtures run in CI without model access. Done.

Not included in v0.6:

- Semantic parsing for every programming language or document format.
- Automatic trust of instructions found in source material.
- Trace collection from a live Agent runtime.
- LLM-assisted source synthesis.

## v0.7 Direction

The next release should focus on policy profiles and stronger validation before adding a hosted
surface. Candidate work includes configurable lint policies, source-aware eval generation,
provider health checks, and the first real Agent runtime adapter.

## Detailed Completion Table

| Component | Done | Remaining |
|---|---|---|
| CLI command structure | `init`, `ingest`, `plan`, `generate`, `lint`, `eval`, `repair`, schema commands, `registry`, `export`, `install` | CLI completion and shell ergonomics |
| Eval command | Default `evals/evals.json`, `--json`, `--markdown`, `--markdown-output`, `--eval-file`, `--no-lint`, `--runner`, `--baseline-skill` | Real Agent runtime adapters |
| Eval validation | Internal validation plus published `docs/eval-schema.json` for trigger, task, and runner tests | Editor examples and schema-version migration policy |
| Repair loop | Repair planning, deterministic edits, rerun checks, rollback on regression, manual security blocks | LLM-assisted proposals and richer patch previews |
| LLM provider layer | Ollama and OpenAI-compatible providers | Provider health checks, streaming, richer errors |
| Skill planning | Manual, LLM, and deterministic source/trace plans with versioned JSON | Confidence reporting and plan migrations |
| Skill writer | `SKILL.md`, `agents/openai.yaml`, optional resources, source index | Better domain templates |
| Naming rules | Hyphen-case normalization and validation | Configurable naming policies |
| Frontmatter parser | Minimal YAML-like parsing for simple metadata | More robust diagnostics and line numbers |
| Linter | Description, folder match, body length, missing resources, dangerous and prompt-injection patterns | Policy profiles and duplicate-content checks |
| Runner layer | Dry-run runner and optional LLM runner | Real Agent runtime adapters, trace collection, cost metrics |
| Local registry | JSON registry, source hashes, risk/eval metadata | Signing, trust policy, dependency metadata |
| Export/install | Direct export and registry-based install to local client directories | Packaged archives and hosted registry adapters |
| Source/trace ingestion | Recursive bounded reads, deterministic extraction, Trace validation, hashes, review notes | More formats and source-aware eval generation |
| Tests | Unit tests and offline fixtures for CLI, ingestion, generation, lint, planning, eval, repair, runner, registry, schema | Fixture matrix and CI coverage expansion |
| Documentation | Indexed architecture, ingestion, format, eval, repair, registry, security, roadmap, and bilingual README | More contributor examples |
| CI | Compile and unit-test matrix for Python 3.10-3.12 on Linux and Windows | Add packaging and type checks when tool choices stabilize |

## Prioritized Backlog

1. Add lint policy profiles.
2. Add source-aware eval generation from examples and failure cases.
3. Add a real Agent runtime adapter for evals and trace collection.
4. Add model-graded evals, cost, latency, and tool-call metrics.
5. Add LLM-assisted repair proposals behind the existing bounded repair gate.
6. Add signed export packages and registry trust policy.
