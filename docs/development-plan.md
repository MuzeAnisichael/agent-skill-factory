# Development Plan

The [roadmap](../ROADMAP.md) is the single source of truth for release scope and completion state.
This document defines product and engineering gates, not a second percentage-based schedule.

## Product Goal

Provide a small reusable core for students and research developers to create useful Skills
from task material, review them, verify what can be checked locally, and export them to an Agent.
A future generation/management/review/optimization/sharing platform should embed this core.

## Design Constraints

- Python 3.10+, local file-based CLI; no database or service is needed for the current lifecycle.
- One runtime dependency, PyYAML, replaces ad hoc YAML parsing. Build tools are development-only.
- Model access is optional. Offline generation, linting and package evaluation remain available.
- Model output is reviewed data. Writing a script is not authorization to execute it.
- Keep domain examples separate from the runtime; avoid a growing template engine or plugin framework.
- Separate package correctness, integration correctness and actual Agent effectiveness.

## Delivery History

| Version | Delivered surface | Still not implied |
|---|---|---|
| v0.1-v0.2 | CLI, generation, lint, optional LLM planning and local evals | Production-grade content or Agent success |
| v0.3 | Local registry, export and install | Signed or hash-verified installation |
| v0.4 | Runner-backed checks and comparison | A first-party Agent integration |
| v0.5 | Deterministic bounded repair and rollback | Persistent snapshots or held-out improvement |
| v0.6 | Source and successful/failed trace ingestion | Automatic live trace capture |
| v0.7 | Lint policies, eval drafts, provider health and generic subprocess protocol | Sandboxed Agent execution |
| v0.8 | Safe format handling, Chinese cues, concrete plans, practical examples and install tests | Field-validated generation quality |

## v0.8 Acceptance Gates

1. Common YAML constructs, quoting, Unicode and optional metadata survive parsing and repair.
2. Invalid types, duplicate keys, unsupported names and specification length violations fail clearly.
3. An old schema-version-1 plan remains readable; new fields are additive and documented.
4. A reviewed plan writes its real workflow/resources; an incomplete plan remains an explicit draft.
5. Generated resources cannot select paths outside the package, portable name rules are checked,
   and symlink/file-directory conflicts are rejected before writing.
6. Three examples pass strict lint and package checks; the CSV helper executes correctly on clean,
   malformed and contract-violating data without modifying input.
7. Source archives and wheels install into separate clean environments and pass the local lifecycle.
8. Bilingual README, architecture, changelog and roadmap accurately describe current limits.

Verification details: [v0.8.0](releases/v0.8.0.md).

## Next Release Gates

**v0.9** requires independent real Agent evidence, not more keyword tests. Choose one runtime,
capture artifacts and traces, separate train/development/held-out cases, and compare no-Skill,
manual-Skill and generated-Skill outcomes. Define task success before optimizing the generator.

**v0.10** requires verifiable distribution: install-time hashes, manifests, review/version records,
tampering tests and reversible upgrades. Signatures are meaningful only with a specified trust model.

**Platform pilot** requires real student/lab feedback first. Keep UI/account/share concerns outside
this package; reuse its plan, lint, eval and export contracts rather than duplicating them.

## Scope Changes and Release Process

Discuss substantial feature scope before implementation. Use a focused branch, update tests and
both README languages, build the distributions, run clean-install checks, push through the local
CLI and review CI before merging/releasing. Do not publish to PyPI without a separate decision.

Local regression tests are engineering evidence. A passing dry-run or auto-repair on the same
assertions is not evidence that a Skill improves an Agent's decisions.
