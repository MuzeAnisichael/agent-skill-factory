# Architecture

Agent Skill Factory is a Python package and CLI, not a hosted Agent runtime.
The design keeps one compact package and local JSON/Markdown/YAML files.

## Current Flow

```text
task material / supplied traces
    -> ingestion or manual/LLM planning
    -> reviewed SkillPlan
    -> deterministic writer
    -> lint and package/runner evals
    -> bounded repair with reruns
    -> local registry and export/install
```

A future platform may call these same functions behind a local or cloud interface.
Accounts, collaboration, queues and public sharing are outside the current core.

## Module Boundaries

| Modules | Responsibility |
|---|---|
| `cli.py` | Argument parsing and explicit lifecycle commands |
| `models.py` | Small data records including plans, resources and findings |
| `ingestion.py`, `extractors.py`, `traces.py` | Bounded source reading, extraction, trace validation and provenance |
| `planner.py`, `llm.py` | Reviewed JSON plans and optional Ollama/OpenAI-compatible transport |
| `generator.py`, `naming.py` | Deterministic package writes and portable naming/path checks |
| `frontmatter.py`, `linter.py`, `policies.py`, `security.py` | Safe YAML, specification and advisory checks, pattern-based risk rules |
| `evaluator.py`, `eval_generation.py`, `runner.py`, `schemas.py` | Eval contracts, drafts, reports, comparison and three runner types |
| `repair.py` | Bounded deterministic edits, reruns and in-memory rollback |
| `registry.py` | Local JSON index, hashes, metadata and copying/export |

There is no service container, database, template framework or automatic tool catalog.
The design does not classify Skills into formal knowledge/workflow/tool categories.

## Planning and Generation

Manual planning accepts a brief, description, repeated `--step`/`--check` and examples.
LLM planning requests concrete steps, checks and complete optional resources as JSON.
Source ingestion extracts summaries/rules/provenance; users must supply/review concrete steps.

Schema version 1 gains optional `workflow`, `quality_checks`, and `resource_files` fields.
A resource contains a portable relative path, full content and loading/execution purpose.
Plans without a workflow remain readable but generate a draft warning.
Details: [Skill Output Format](skill-output-format.md).

The writer uses safe YAML serialization for frontmatter and quoted Codex `interface` metadata.
Requested resource directories can remain empty; no fake helper or placeholder template is added.
Source-backed plans also write a compact source index without copying source documents.
All write destinations are preflighted for path escapes, symlinks and file/directory conflicts.

## Validation

YAML is loaded through a SafeLoader subclass that rejects duplicate/non-string mapping keys.
Linter errors cover required/optional field types, naming, length limits, missing resources and
Python syntax. English/Chinese trigger cues and weighted description length are advisory heuristics.
Strict policy promotes known warnings, including unfinished drafts, to errors.

The linter is not a complete security analysis and does not verify declared script dependencies,
numerical correctness or every client-specific extension. It does not provide execution isolation.

## Evaluation Boundaries

- Trigger tests use keyword/word overlap heuristics, not an Agent's skill-selection behavior.
- Task assertions check package text, not task completion.
- Dry-run runner echoes supplied instructions to test protocol plumbing.
- LLM runner sends the main instructions as text, without automatic resource/tool execution.
- Subprocess runner integrates a user-supplied process over JSON stdin/stdout, without a sandbox.

Baseline comparison and score deltas use the configured assertions. Actual runtime artifacts,
tool traces, cost metrics and independent quality benchmarks are planned for v0.9.
See [Evaluation Strategy](evaluation.md) and [Runner Adapters](runner-adapters.md).

## Repair and Distribution

Repair can expand descriptions while preserving supported YAML metadata, create missing references,
split long bodies, and append terms requested by positive eval assertions. Invalid YAML and security
findings require manual review. Acceptance checks the same lint/eval set; it is not held-out
optimization. Rollback is immediate and local, not persistent version history.

Registry entries record hashes and eval/risk status. Export/install copy local files; install does
not yet verify that the indexed source still matches recorded hashes. Signing, manifests and trust
policy are planned for v0.10. See [Registry and Export](registry.md).

## Dependencies and Verification

PyYAML is the only runtime dependency. Provider transports, fixtures, examples and CLI use Python
standard-library facilities otherwise. Domain examples live in `examples/`, not new runtime modules.

CI tests Python 3.10-3.12 on Linux/Windows. Separate packaging jobs build an sdist and wheel and
exercise both in fresh virtual environments from outside the source checkout.
See [v0.8 verification](releases/v0.8.0.md) for reproducible commands and evidence limits.
