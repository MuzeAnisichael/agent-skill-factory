# Source and Trace Ingestion

`v0.6.0` adds a deterministic path from local documents and Agent traces to a reviewable
`SkillPlan`. Ingestion does not require an LLM and does not write a Skill package directly.

## Workflow

```text
documents / code / traces -> ingest -> review SkillPlan JSON -> generate --from-plan -> lint / eval
```

Create a plan from files or directories:

```bash
skill-factory ingest docs src/example.py \
  --trace traces/release.trace.json \
  --name "Release Note Builder" \
  --output skill-plan.json
```

Review `skill-plan.json`, then generate the Skill:

```bash
skill-factory generate --from-plan skill-plan.json --output skills
skill-factory lint skills/release-note-builder
```

`--from-plan` cannot be combined with manual or LLM planning flags. This makes the reviewed JSON
the single input to generation.

## Extracted Plan Data

The versioned `SkillPlan` JSON contains:

| Field | Purpose |
|---|---|
| `examples` | Trigger examples from task/example sections and successful traces |
| `constraints` | Explicit must/should/never rules and trace constraints |
| `terminology` | Backtick terms and glossary entries |
| `tool_candidates` | Tools observed in traces; candidates, not authorization |
| `failure_cases` | Failed tasks with compact error context |
| `sources` | Relative display path, kind, byte size, and SHA-256 digest |
| `review_notes` | Unsafe source lines omitted from generated instructions |

Extraction is intentionally conservative and deterministic. It recognizes Markdown headings,
list items, explicit English and Chinese constraint markers, UTF-8 text, and the published Trace
schema. The plan remains editable because no heuristic can infer every domain rule correctly.

## Source Handling

Directories are scanned recursively in a stable order. Common text, documentation, configuration,
and source-code extensions are supported. Hidden directories, VCS metadata, virtual environments,
build output, and `node_modules` are ignored.

Default ingestion limits are:

- 100 files
- 1,000,000 bytes per file
- 5,000,000 bytes in total

Use `--max-files`, `--max-file-bytes`, and `--max-total-bytes` to set tighter or larger explicit
limits. Binary and non-UTF-8 inputs are rejected rather than decoded silently.

## Trace Format

Trace files use schema version 1:

```json
{
  "schema_version": 1,
  "runs": [
    {
      "id": "release-001",
      "task": "Draft release notes from approved pull requests.",
      "status": "success",
      "summary": "Grouped changes by customer impact.",
      "tools": ["git log", "repository search"],
      "constraints": ["Only include reviewed pull requests."]
    },
    {
      "id": "release-002",
      "task": "Publish notes with incomplete source data.",
      "status": "failure",
      "error": "The release date was missing."
    }
  ]
}
```

Print or write the canonical schema with:

```bash
skill-factory trace-schema
skill-factory trace-schema --output docs/trace-schema.json
```

See [trace-schema.json](trace-schema.json) for the complete contract.

## Attribution and Safety

Generated source-backed Skills write `references/sources.md`. It records source hashes and compact
extractions but does not copy the indexed files. `SKILL.md` contains only the concise objective,
extracted rules, workflow, and examples.

Source documents and traces are untrusted input. Lines matching destructive, exfiltration,
approval-bypass, or prompt-injection patterns are excluded from extracted instructions and listed
in `review_notes`. This is a guardrail, not a proof of safety; run `lint` and task-specific evals
before installing the generated Skill.
