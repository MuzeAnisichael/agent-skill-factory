# Roadmap and Completion Table

Agent Skill Factory is developed in small, testable milestones. The near-term goal is a reliable local CLI before any hosted service or marketplace work.

Current version target completed in this repository: `v0.7.0`.

## Completion Summary

| Milestone | Status | Completion | Evidence | Next Step |
|---|---:|---:|---|---|
| M0 Repository and spec | Done | 100% | README, docs, MIT license, security model | Keep docs aligned with implementation |
| M1 Local CLI skeleton | Done | 100% | `skill-factory init`, `generate`, `lint` | Improve CLI ergonomics |
| M1.5 LLM planning | Done | 100% | `plan`, `generate --llm`, provider health, Ollama and OpenAI-compatible clients | Add streaming only when a workflow needs it |
| M2 Static linter | In progress | 85% | Core checks plus built-in and custom policy profiles | Add duplicate-content and dependency checks |
| M3 Local eval runner | In progress | 85% | Eval drafts, trigger/task/runner cases, schema, reports, regression comparison | Add model-graded and structured trace evals |
| M3.5 Local registry and export | Done | 100% | `registry add/list/show`, `export`, `install`, source hashes, risk and eval metadata | Add signing and trust policies later |
| M3.8 Runner-backed evals | Done | 100% | Dry-run, LLM, and subprocess runners; with/without Skill and baseline comparison | Add first-party runtime adapters later |
| M4 Repair loop | Done | 100% | `repair plan`, `repair apply`, bounded edits, rollback on regression | Add LLM-assisted repair proposals later |
| M5 Source and trace ingestion | Done | 100% | `ingest`, Trace schema, versioned plans, source hashes, review notes | Broaden extractors from real usage |
| M5.5 Runtime integration | In progress | 50% | Generic JSON subprocess adapter | Add trace capture, tool events, and isolation guidance |
| M6 Hosted/web surface | Later | 0% | Out of initial scope | Defer until policy and runtime gates mature |

## v0.7.0 Scope

Goal: turn source-grounded Skill plans into configurable, operational quality gates.

Completed:

- Added standard, strict, permissive, and custom JSON lint policies.
- Added source-aware eval draft generation from reviewed `SkillPlan` data.
- Added read-only provider connectivity and model availability diagnostics.
- Added a generic subprocess Agent runner with a documented JSON protocol.
- Added structured runner failure reporting and offline tests for every new boundary.

Acceptance criteria:

- Teams can enforce stricter lint behavior without forking the linter. Done.
- Ingested examples and failures can seed a schema-valid eval file without model access. Done.
- Users can diagnose Ollama or API model discovery before generation. Done.
- An external Agent can participate in with/without-Skill evals through a stable process boundary. Done.

Not included in v0.7:

- First-party adapters for individual Agent CLIs or SDKs.
- Automatic live trace and structured tool-call capture.
- Process sandboxing or remote execution.
- Signed packages and registry trust policy.

## v0.8 Direction

The next release should harden distribution and runtime evidence before adding a hosted surface.
Candidate work includes signed export manifests, registry trust policies, structured Agent trace
capture, one first-party runtime adapter, and dependency/capability declarations.

## Detailed Completion Table

| Component | Done | Remaining |
|---|---|---|
| CLI command structure | `init`, `ingest`, `plan`, `provider-health`, `generate`, `lint`, `eval-generate`, `eval`, `repair`, schema commands, `registry`, `export`, `install` | CLI completion and shell ergonomics |
| Eval command | Eval drafts, reports, custom files, lint aggregation, three runners, and baseline comparison | First-party Agent adapters and model grading |
| Eval validation | Internal validation plus published `docs/eval-schema.json` for trigger, task, and runner tests | Editor examples and schema-version migration policy |
| Repair loop | Repair planning, deterministic edits, rerun checks, rollback on regression, manual security blocks | LLM-assisted proposals and richer patch previews |
| LLM provider layer | Ollama and OpenAI-compatible generation plus health checks | Streaming and richer compatibility diagnostics |
| Skill planning | Manual, LLM, and deterministic source/trace plans with versioned JSON | Confidence reporting and plan migrations |
| Skill writer | `SKILL.md`, `agents/openai.yaml`, optional resources, source index | Better domain templates |
| Naming rules | Hyphen-case normalization and validation | Configurable naming policies |
| Frontmatter parser | Minimal YAML-like parsing for simple metadata | More robust diagnostics and line numbers |
| Linter | Core checks plus built-in and custom policy profiles | Duplicate-content and dependency checks |
| Runner layer | Dry-run, optional LLM, and generic subprocess Agent runners | First-party adapters, trace collection, isolation, cost metrics |
| Local registry | JSON registry, source hashes, risk/eval metadata | Signing, trust policy, dependency metadata |
| Export/install | Direct export and registry-based install to local client directories | Packaged archives and hosted registry adapters |
| Source/trace ingestion | Bounded reads, extraction, validation, hashes, review notes, and source-aware eval drafts | More formats and live trace collection |
| Tests | 70 offline unit and CLI tests across the local lifecycle | Fixture matrix and CI coverage expansion |
| Documentation | Indexed architecture, ingestion, format, eval, repair, registry, security, roadmap, and bilingual README | More contributor examples |
| CI | Compile and unit-test matrix for Python 3.10-3.12 on Linux and Windows | Add packaging and type checks when tool choices stabilize |

## Prioritized Backlog

1. Add signed export manifests and registry trust policy.
2. Add structured trace and tool-call capture to the runner protocol.
3. Add one first-party Agent runtime adapter with isolation guidance.
4. Add model-graded evals, cost, latency, and tool-call metrics.
5. Add capability and dependency declarations to Skill metadata.
6. Add LLM-assisted repair proposals behind the existing bounded repair gate.
