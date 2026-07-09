# Evaluation Strategy

A Skill is useful only if it improves Agent behavior. The project now includes local package evals plus runner-backed evals. The default runner is deterministic and network-free, while an optional LLM runner can call Ollama or an OpenAI-compatible API when explicitly requested.

## Current Command

```bash
skill-factory eval path/to/skill
skill-factory eval path/to/skill --json
skill-factory eval path/to/skill --markdown
skill-factory eval path/to/skill --markdown-output eval-report.md
skill-factory eval path/to/skill --eval-file path/to/evals.json
skill-factory eval path/to/skill --no-lint
skill-factory eval path/to/skill --runner dry-run
skill-factory eval path/to/skill --runner llm --provider ollama --model llama3.1
skill-factory eval path/to/skill --baseline-skill old/path/to/skill
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
  ],
  "runner_tests": [
    {
      "id": "skill-context-improves-release-note-output",
      "prompt": "Create release notes for the current branch.",
      "assertions": [
        {"target": "output", "contains": "features section"},
        {"target": "output", "contains": "fixes section"}
      ],
      "baseline_assertions": [
        {"target": "output", "contains": "No Skill context was loaded"}
      ],
      "require_improvement": true,
      "min_score_delta": 2
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
- `runner_tests`

Unknown top-level keys are rejected. At least one trigger, task, or runner case is required.

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

Runner case fields:

| Field | Required | Type |
|---|---:|---|
| `id` | yes | non-empty string |
| `prompt` | yes | non-empty string |
| `assertions` | yes | non-empty array |
| `baseline_assertions` | no | array |
| `require_improvement` | no | boolean, default `true` |
| `min_score_delta` | no | non-negative integer |

Runner assertion targets:

- `output`: runner output. This is the default.
- `text`: alias for runner output.

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

### Runner Eval

Runs the same prompt twice:

1. without Skill context
2. with Skill context

The default `dry-run` runner is deterministic. It emits a baseline output with no Skill context and a with-Skill output containing the Skill name, description, and body. This makes CI stable while still proving that the Skill carries useful task context.

The optional `llm` runner calls a configured LLM provider:

```bash
skill-factory eval skills/release-note-builder \
  --runner llm \
  --provider ollama \
  --model llama3.1
```

Use the LLM runner only when model access is available. CI should continue to use `dry-run`.

Runner scoring:

- `assertions` are scored against both baseline output and with-Skill output.
- The with-Skill output must pass all `assertions`.
- When `require_improvement` is true, the with-Skill score must improve over the baseline score by at least `min_score_delta`.
- `baseline_assertions`, when present, must pass against the baseline output.

### Regression Comparison

Use `--baseline-skill` to compare a candidate Skill against an older Skill with the same eval file:

```bash
skill-factory eval skills/release-note-builder --baseline-skill old-skills/release-note-builder
```

The comparison passes when the candidate eval passes and the candidate does not score lower than the baseline.

### Markdown Reports

Markdown reports are useful for issue comments, pull requests, and manual review:

```bash
skill-factory eval skills/release-note-builder --markdown
skill-factory eval skills/release-note-builder --markdown-output eval-report.md
```

### Lint Aggregation

By default, `skill-factory eval` also runs static lint and fails the report if lint has errors. Use `--no-lint` for isolated eval debugging.

## Planned Eval Types

### Baseline Eval

Current runner behavior:

- Run each runner task without the Skill.
- Run the same task with the Skill.
- Compare assertion pass counts.
- Compare a candidate Skill against a baseline Skill.

Future work should add model-graded quality, latency, tool-call, and safety metrics.

### Agent-Backed Eval

Future support should integrate with actual Agent runtimes so the runner can evaluate tool use, trace quality, and task outcomes beyond text assertions.

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
- Runner assertion score delta.
- Regression score delta.
- Lint pass/fail.
- Total passed and failed cases.
- Eval configuration validation.
- Markdown reports.

Planned:

- Trigger precision and recall.
- Task pass rate.
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
