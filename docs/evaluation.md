# Evaluation Strategy

A Skill is useful only if it improves Agent behavior. Evaluation must compare behavior with and without the Skill.

## Eval Types

### Trigger Eval

Tests whether the Skill activates on relevant prompts and stays inactive on near-misses.

```json
[
  {
    "query": "Generate a release note from this repo's merged PRs.",
    "should_trigger": true
  },
  {
    "query": "Explain what release notes are.",
    "should_trigger": false
  }
]
```

### Task Eval

Tests whether the Skill helps complete realistic work.

```json
{
  "id": "release-note-basic",
  "prompt": "Create release notes for the current branch.",
  "expected_output": "A concise release note with features, fixes, and risks.",
  "files": [],
  "assertions": [
    "The output includes a features section.",
    "The output cites concrete changes.",
    "The output does not invent unrelated work."
  ]
}
```

### Baseline Eval

Runs each task twice:

- without Skill
- with Skill

For revisions, compare:

- old Skill
- new Skill

### Safety Eval

Attempts to trigger unsafe behavior:

- Broad file deletion.
- Secret exfiltration.
- External posting.
- Production deployment.
- Unapproved shell commands.

## Metrics

- Trigger precision and recall.
- Task pass rate.
- Regression count.
- Token cost.
- Runtime.
- Tool-call count.
- Safety violation count.

## Acceptance Rule

A generated or repaired Skill should be accepted only when:

- It passes static lint.
- It improves or preserves held-out eval score.
- It does not increase risk level without explicit approval.
- It does not materially increase token cost without quality gain.
