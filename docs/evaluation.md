# Evaluation Strategy

A Skill is useful only if it improves Agent behavior. The project now includes an initial local eval runner. It is intentionally lightweight: it validates trigger behavior and task assertions against the Skill package before future Agent-backed evals are added.

## Current Command

```bash
skill-factory eval path/to/skill
skill-factory eval path/to/skill --json
skill-factory eval path/to/skill --eval-file path/to/evals.json
skill-factory eval path/to/skill --no-lint
skill-factory eval-schema
skill-factory eval-schema --output docs/eval-schema.json
```

Default eval path:

```text
<skill>/evals/evals.json
```

## Eval File Shape

```json
{
  "trigger_tests": [
    {
      "id": "release-notes-from-prs",
      "query": "Create release notes from the merged pull requests.",
      "should_trigger": true,
      "keywords": ["release notes", "pull requests"]
    },
    {
      "id": "explain-git",
      "query": "Explain what git is.",
      "should_trigger": false,
      "keywords": ["release notes", "pull requests"]
    }
  ],
  "task_tests": [
    {
      "id": "contains-required-sections",
      "prompt": "Create release notes for the current branch.",
      "assertions": [
        {"target": "body", "contains": "features"},
        {"target": "body", "contains": "fixes"},
        {"target": "body", "not_contains": "rm -rf"}
      ]
    }
  ]
}
```

## Schema Validation

The eval runner validates configuration before executing cases. Invalid eval files fail fast with `EvalError`.

The published JSON Schema lives at [`docs/eval-schema.json`](eval-schema.json). Use `skill-factory eval-schema` to print the same schema from the installed package, or `--output` to write it for editor integration.

Top-level keys:

- `trigger_tests`
- `task_tests`

Unknown top-level keys are rejected. At least one trigger or task case is required.

Trigger case fields:

| Field | Required | Type |
|---|---:|---|
| `id` | yes | non-empty string |
| `query` | yes | non-empty string |
| `should_trigger` | yes | boolean |
| `keywords` | no | array of non-empty strings |
| `negative_keywords` | no | array of non-empty strings |

Task case fields:

| Field | Required | Type |
|---|---:|---|
| `id` | yes | non-empty string |
| `prompt` | no | string |
| `assertions` | yes | non-empty array |

Assertion object fields:

- `target`: optional, one of `text`, `description`, `body`.
- Exactly one operator is required: `contains`, `not_contains`, `any_contains`, or `all_contains`.
- `contains` and `not_contains` use a non-empty string.
- `any_contains` and `all_contains` use a non-empty string array.

## Current Eval Types

### Trigger Eval

Checks whether a Skill should activate for a query.

Supported fields:

- `id`: stable case identifier.
- `query`: user request.
- `should_trigger`: expected boolean.
- `keywords`: optional positive keywords checked against the query.
- `negative_keywords`: optional negative keywords.

When `keywords` is omitted, the runner uses a simple word-overlap fallback between query and Skill text. This is not a substitute for model-based trigger classification, but it catches weak trigger descriptions early.

### Task Eval

Checks whether the Skill package contains required content.

Supported assertion forms:

```json
{"target": "body", "contains": "features"}
{"target": "body", "not_contains": "rm -rf"}
{"target": "text", "any_contains": ["features", "enhancements"]}
{"target": "description", "all_contains": ["release", "notes"]}
```

Targets:

- `text`: frontmatter name, description, and body.
- `description`: frontmatter description.
- `body`: `SKILL.md` body.

### Lint Aggregation

By default, `skill-factory eval` also runs static lint and fails the report if lint has errors. Use `--no-lint` for isolated eval debugging.

## Planned Eval Types

### Baseline Eval

Future runner behavior:

- Run each task without the Skill.
- Run the same task with the Skill.
- Compare quality, latency, tool calls, and safety.

For revisions:

- Compare old Skill vs new Skill.
- Block regressions on held-out evals.

### Agent-Backed Eval

Future support should integrate with actual Agent runtimes so the runner can evaluate behavior instead of only package text.

### Safety Eval

Future safety evals should attempt to trigger:

- Broad file deletion.
- Secret exfiltration.
- External posting.
- Production deployment.
- Unapproved shell commands.

## Metrics

Current:

- Trigger pass/fail.
- Task assertion pass/fail.
- Lint pass/fail.
- Total passed and failed cases.
- Eval configuration validation.

Planned:

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
- It passes local evals.
- It improves or preserves held-out eval score once baseline eval is available.
- It does not increase risk level without explicit approval.
- It does not materially increase token cost without quality gain.
