# Roadmap and Completion Table

Agent Skill Factory is developed in small, testable milestones. The near-term goal is a reliable local CLI before any hosted service or marketplace work.

Current version target completed in this repository: `v0.3.0`.

## Completion Summary

| Milestone | Status | Completion | Evidence | Next Step |
|---|---:|---:|---|---|
| M0 Repository and spec | Done | 100% | README, docs, MIT license, security model | Keep docs aligned with implementation |
| M1 Local CLI skeleton | Done | 100% | `skill-factory init`, `generate`, `lint` | Improve CLI ergonomics |
| M1.5 LLM planning | Done | 100% | `plan`, `generate --llm`, Ollama and OpenAI-compatible clients | Add provider health checks and richer errors |
| M2 Static linter | In progress | 70% | Naming, frontmatter, resource, risk, syntax checks | Add policy profiles and broader unsafe-pattern coverage |
| M3 Local eval runner | In progress | 60% | `eval`, trigger evals, task assertions, strict schema validation, JSON Schema | Add Agent-backed baseline evals and Markdown reports |
| M3.5 Local registry and export | Done | 100% | `registry add/list/show`, `export`, `install`, source hashes, risk and eval metadata | Add signing and trust policies later |
| M4 Repair loop | Planned | 0% | Architecture documented | Add bounded repair plan format |
| M5 Source and trace ingestion | Planned | 0% | Architecture documented | Convert docs/code/traces into structured Skill inputs |
| M6 Hosted/web surface | Later | 0% | Out of initial scope | Revisit after CLI is useful |

## v0.3.0 Scope

Completed:

- Publish `docs/eval-schema.json` for eval file editor/tool integration.
- Add `skill-factory eval-schema`.
- Add a local file-based registry at `.skill-factory/registry.json`.
- Record Skill metadata, version, path, risk summary, eval status, package hash, and file hashes.
- Add `skill-factory registry add/list/show`.
- Add `skill-factory export` for direct Skill package export.
- Add `skill-factory install` for registry-based installation.
- Support `agent-skills`, `codex`, and `claude-code` export targets.
- Add unit tests for registry, export/install, CLI, and schema stability.
- Update README and docs for the implemented lifecycle.

Not included in v0.3:

- Hosted registry.
- Package signing.
- Dependency resolution between Skills.
- Real Agent runtime evals.
- Automatic repair loop.

## v0.4 Development Plan

Goal: make evals measure actual Agent behavior, not only package text.

Planned work:

- Add a runner abstraction for task execution.
- Add a local dry-run runner for deterministic tests.
- Add optional LLM/Agent-backed runner integration.
- Compare without-skill vs with-skill outputs.
- Emit Markdown eval reports for review.
- Add regression gates for old Skill vs new Skill.

Acceptance criteria:

- A sample Skill can show measurable improvement over baseline.
- Failed evals produce actionable diagnostics.
- Eval fixtures run in CI without external network requirements.
- Optional model-backed evals are skipped unless explicitly configured.

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
| CLI command structure | `init`, `plan`, `generate`, `lint`, `eval`, `eval-schema`, `registry`, `export`, `install` | `repair`, runner-backed eval commands, ingestion commands |
| Eval command | Default `evals/evals.json`, `--json`, `--eval-file`, `--no-lint` | Agent-backed baseline evals and Markdown reports |
| Eval validation | Internal validation plus published `docs/eval-schema.json` | Editor examples and schema-version migration policy |
| LLM provider layer | Ollama and OpenAI-compatible providers | Provider health checks, streaming, richer errors |
| Skill planning | LLM-generated structured `SkillPlan` | Plan validation, source attribution, confidence reporting |
| Skill writer | `SKILL.md`, `agents/openai.yaml`, optional resource dirs | Better templates, source attribution, deterministic plan files |
| Naming rules | Hyphen-case normalization and validation | Configurable naming policies |
| Frontmatter parser | Minimal YAML-like parsing for simple metadata | More robust diagnostics and line numbers |
| Linter | Description, folder match, body length, missing resources, dangerous patterns | Policy profiles, more unsafe patterns, duplicate-content checks |
| Local registry | JSON registry, source hashes, risk/eval metadata | Signing, trust policy, dependency metadata |
| Export/install | Direct export and registry-based install to local client directories | Packaged archives and hosted registry adapters |
| Tests | Unit tests for CLI, generation, linter, naming, LLM planning, local eval, registry, schema | Fixture matrix and CI coverage expansion |
| Documentation | Architecture, format, eval, registry, security, roadmap, bilingual README | Contributor walkthroughs and more examples |
| CI | Workflow file added | Add lint/type checks when tool choices stabilize |

## Prioritized Backlog

1. Add Agent-backed eval runner abstraction.
2. Add Markdown eval reports.
3. Add lint policy profiles.
4. Add repair-loop prototype.
5. Add source/document ingestion into structured Skill inputs.
6. Add signed export packages and registry trust policy.
