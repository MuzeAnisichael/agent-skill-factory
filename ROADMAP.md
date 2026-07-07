# Roadmap and Completion Table

Agent Skill Factory is developed in small, testable milestones. The near-term goal is a reliable local CLI before any hosted service or marketplace work.

## Completion Summary

| Milestone | Status | Completion | Evidence | Next Step |
|---|---:|---:|---|---|
| M0 Repository and spec | Done | 100% | README, docs, MIT license, security model | Keep docs aligned with implementation |
| M1 Local CLI skeleton | Done | 100% | `skill-factory init`, `generate`, `lint` | Improve CLI UX and examples |
| M2 Static linter | In progress | 65% | Naming, frontmatter, resource, risk, syntax checks | Add fixture-based rule coverage and configurable policies |
| M3 Eval runner | Planned | 0% | Eval strategy documented | Define eval schema and local runner |
| M4 Repair loop | Planned | 0% | Architecture documented | Add bounded repair plan format |
| M5 Registry and export | Planned | 0% | Registry shape documented | Implement local registry index |
| M6 Hosted/web surface | Later | 0% | Out of initial scope | Revisit after CLI is useful |

## Development Plan

### Phase 1: Local Skill Factory

Goal: make local Skill generation and validation dependable.

- Generate a standards-aligned Skill package from a structured brief.
- Validate `SKILL.md` frontmatter, naming, body length, resource references, and unsafe instructions.
- Produce human-readable and JSON lint reports.
- Keep runtime dependencies at zero unless a dependency is clearly justified.

Current status: partially complete. The CLI, writer, and initial linter are implemented.

### Phase 2: Evaluation Runner

Goal: prove whether a Skill improves Agent behavior.

- Add an `evals/evals.json` convention.
- Support trigger evals with should-trigger and should-not-trigger cases.
- Support task evals with assertions.
- Compare without-skill vs with-skill runs through a runner abstraction.
- Emit Markdown and JSON reports.

Acceptance criteria:

- A sample Skill can show measurable improvement over baseline.
- Failed evals produce actionable diagnostics.
- Eval fixtures run in CI.

### Phase 3: Repair Loop

Goal: make generated Skills iteratively better without rewriting them blindly.

- Convert lint and eval failures into bounded edit plans.
- Apply small changes to `SKILL.md` or resource files.
- Re-run lint and eval after each repair.
- Accept a repair only if held-out quality is preserved or improved.

Acceptance criteria:

- The system can improve a weak description.
- The system can split oversized body content into `references/`.
- The system refuses changes that increase risk without approval.

### Phase 4: Local Registry and Export

Goal: make Skills manageable across projects and Agent clients.

- Add a file-based registry index.
- Track version, risk level, source hashes, eval score, and export targets.
- Export to `.agents/skills/`.
- Add adapters for `.claude/skills/` and Codex-style user skill directories.

Acceptance criteria:

- Users can generate, lint, register, and install a Skill locally.
- Registry metadata is deterministic and reviewable.

## Detailed Completion Table

| Component | Done | Remaining |
|---|---|---|
| CLI command structure | `init`, `generate`, `lint` | `eval`, `repair`, `registry`, `export` |
| Skill writer | `SKILL.md`, `agents/openai.yaml`, optional resource dirs | Better templates, source attribution, deterministic plan files |
| Naming rules | Hyphen-case normalization and validation | Configurable naming policies |
| Frontmatter parser | Minimal YAML-like parsing for simple metadata | More robust diagnostics and line numbers |
| Linter | Description, folder match, body length, missing resources, dangerous patterns | Policy profiles, more unsafe patterns, duplicate-content checks |
| Tests | Unit tests for CLI, generation, linter, naming | Fixture matrix and CI coverage expansion |
| Documentation | Architecture, format, eval, security, roadmap | More examples and contributor walkthroughs |
| CI | Workflow file added | Badges turn green after first GitHub Actions run |

## Prioritized Backlog

1. Add fixture Skills under `tests/fixtures/`.
2. Add JSON schema for eval files.
3. Implement `skill-factory eval`.
4. Add policy profiles for lint strictness.
5. Implement local registry metadata.
6. Add export adapters.
7. Add repair-loop prototype.
