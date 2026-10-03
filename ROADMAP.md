# Roadmap and Completion Table

Agent Skill Factory is a local-first, headless core for creating, checking and distributing
Skills. Students and early-career research developers are the initial audience.
Current version: **v0.8.0 (alpha)**.

## Evidence States

We use evidence instead of completion percentages:

- **Implemented**: code and focused offline tests exist.
- **Integration verified**: the local end-to-end workflow or executable helper has been exercised.
- **Field validated**: independent real Agent tasks or user trials provide evidence.
- **Released**: a GitHub tag and release artifacts identify a tested version.

Implemented features are not automatically field validated. No real Agent quality uplift is
claimed by the offline test count or dry-run scores.

## Completion Table

| Component | Current evidence | Remaining boundary |
|---|---|---|
| CLI and local lifecycle | Integration verified: unit/CLI tests and clean wheel/source installs | Wider user trials |
| Source/trace ingestion | Implemented: bounded reads, hashes, versioned traces and source plans | Live trace capture and more formats |
| Ollama/API planning | Implemented: provider tests and structured plan parsing | Real-model quality, cost and reliability studies |
| Skill generation | Integration verified: workflow/check/resource plans and three maintained examples | Domain-specific generation effectiveness |
| Format validation | Implemented: safe YAML, optional fields, type/length/name checks, Chinese cues | Broader compatibility fixtures, not a sandbox |
| Evaluation | Implemented: heuristic triggers, package assertions, dry-run/LLM/subprocess runners | Independent task/artifact/trace evaluation |
| Repair | Implemented: bounded edits, reruns and rollback | Held-out acceptance and persistent history |
| Local registry/export/install | Integration verified: local metadata and file copy lifecycle | Hash verification at install, manifests and trust policies |
| Packaging/CI | Integration verified locally: source archive and wheel; CI tests Linux/Windows | Published PyPI package is not in scope |
| Hosted platform | Planned only | User demand and core evidence gates |

Evidence: [tests](tests), [examples](examples/README.md),
[CI workflow](.github/workflows/ci.yml), [v0.8 verification](docs/releases/v0.8.0.md),
[GitHub releases](https://github.com/MuzeAnisichael/agent-skill-factory/releases).

## v0.8: Standards and Practical Generation

- [x] Replace minimal parsing with safe YAML and duplicate-key diagnostics.
- [x] Validate standard optional fields, metadata types, lengths and single-hyphen names.
- [x] Support Chinese trigger descriptions without English-only phrase requirements.
- [x] Add editable workflow steps, observable checks and complete resource contents to plans.
- [x] Stop generating placeholder helpers/templates; mark incomplete workflows as drafts.
- [x] Correct Codex interface metadata and preserve optional YAML during description repair.
- [x] Add Python review, experimental CSV checks and report consistency examples.
- [x] Test package builds and clean installation of both distribution formats.
- [x] Align bilingual READMEs, architecture, migration notes and evaluation limitations.

Not included: web UI, cloud accounts, first-party Agent adapters, automatic model-code execution,
runtime sandboxing, signing, PyPI publication, or claims of proven Agent improvement.

## v0.9: Real Agent Evidence

Priority: establish whether the generated Skills actually help.

1. Select one first-party Agent adapter from the initial users' environment; do not assume a vendor.
2. Capture task outputs, artifacts and tool events with explicit execution authorization.
3. Use independent development and held-out test sets, including positive/negative routing cases.
4. Compare no-Skill, manually authored Skill and generated Skill on the same tasks and settings.
5. Measure task success, regressions, latency and cost; do not score simple instruction echoes.
6. Prevent repair from treating inserted assertion strings as proof of behavioral improvement.

Exit gate: reproducible results on a small student/research task set, including failures and
the limits of the chosen runtime. Adapter integration alone does not satisfy this gate.

## v0.10: Reliable Distribution

1. Verify package hashes at installation; refuse changed registry sources by default.
2. Export versioned manifests and record provenance, review decisions and repair history.
3. Define trust policies and capability declarations without implying they enforce a sandbox.
4. Add signing only after the verifier and key/trust model have concrete users.

Exit gate: reproducible install/upgrade/rollback and tampering tests.
Cross-client compatibility must be stated by tested versions, not assumed.

## Platform Pilot: After Evidence

Keep this repository the shared core. Build a separate thin local or hosted interface only after
course/lab pilots establish the workflows worth supporting: generation, inventory, review,
optimization and sharing. Start with local workspaces and explicit review records; defer a
public marketplace, multi-tenant execution and billing until there is demand and a threat model.

## Development Order

v0.8 usability and compatibility -> v0.9 task evidence -> v0.10 trustworthy distribution ->
small platform pilot. Revisit each scope with users before implementation.

Detailed product boundaries and engineering gates: [Development Plan](docs/development-plan.md).
