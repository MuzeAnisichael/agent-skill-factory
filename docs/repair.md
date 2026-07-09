# Repair Loop

`v0.5.0` adds a bounded repair loop for generated Skills.

The repair loop is intentionally conservative:

- It creates an explicit repair plan before editing files.
- It applies only deterministic, narrow edits.
- It reruns lint and eval after editing.
- It rolls changes back when lint or eval quality regresses.
- It refuses security-related findings by default and marks them for manual review.

## Commands

Create a plan without editing files:

```bash
skill-factory repair plan skills/release-note-builder
skill-factory repair plan skills/release-note-builder --json
```

Apply safe repairs:

```bash
skill-factory repair apply skills/release-note-builder
```

Plan or apply with eval options:

```bash
skill-factory repair plan skills/release-note-builder --eval-file path/to/evals.json
skill-factory repair apply skills/release-note-builder --runner dry-run
skill-factory repair apply skills/release-note-builder --no-eval
skill-factory repair apply skills/release-note-builder --dry-run
```

## Repair Plan Shape

```json
{
  "skill_path": "skills/release-note-builder",
  "actionable_count": 2,
  "actions": [
    {
      "id": "description.expand",
      "kind": "set_description",
      "path": "skills/release-note-builder/SKILL.md",
      "description": "Expand frontmatter description with clearer trigger context.",
      "reason": "Description should explain when the Skill should be used.",
      "payload": {
        "description": "Use this skill when ..."
      },
      "risky": false
    }
  ],
  "blocked": [],
  "lint": {},
  "eval": {}
}
```

## Supported Automatic Repairs

| Failure | Repair |
|---|---|
| Missing frontmatter description | Add a trigger-oriented description. |
| Weak or short description | Expand the description with trigger context. |
| Missing referenced resource | Create a placeholder file at the referenced path. |
| Oversized `SKILL.md` body | Move overflow content into `references/overflow.md`. |
| Missing positive eval assertion | Add an explicit repair note to the Skill body. |

## Manual Review Cases

Security findings are not auto-applied:

- destructive recursive deletion
- download-and-execute shell pipelines
- secret exfiltration language
- approval, sandbox, or guardrail bypass language
- dangerous script content

These appear as `manual_review` actions in the plan and as `blocked` messages.

## Acceptance Rule

After applying repairs, the command reruns lint and eval.

The repair is accepted only when:

- lint error count does not increase
- eval passed count does not decrease
- at least one lint warning/error count or eval score improves, or quality is preserved after a real applied change

If the acceptance rule fails, the command restores the original `SKILL.md` and removes files created during the failed repair attempt.

## Design Notes

- The repair loop does not call an LLM.
- The source Skill remains the source of truth.
- The repair plan is reviewable JSON.
- The implementation favors small deterministic edits over broad rewrites.
- Future versions can add LLM-generated edit plans, but they should still pass through this bounded plan/apply gate.
