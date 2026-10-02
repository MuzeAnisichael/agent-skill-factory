# Skill Output Format

The portable package targets the [Agent Skills specification](https://agentskills.io/specification).
Codex UI metadata is a separate client-specific extension, not part of the portable core.

## Package Structure

```text
skill-name/
|-- SKILL.md                  required
|-- references/               optional instructions loaded when needed
|-- scripts/                  optional executable helpers
|-- assets/                   optional output templates/data
`-- agents/openai.yaml        generated Codex UI metadata
```

Only create resources with a concrete purpose. `--resources` requests directories, not invented
content. v0.8 no longer writes placeholder `helper.py`, `domain.md` or `template.md`.
With `--force`, existing unrelated files are preserved; manually review/remove obsolete
placeholders in older packages.

## YAML Frontmatter

```yaml
---
name: experiment-csv-check
description: >-
  检查实验 CSV 的列契约和数值合法性，
  用于在统计分析前核查数据质量。
license: MIT
compatibility: Python 3.10+
metadata:
  version: "1.0"
allowed-tools: Read
---
```

Rules:

- `name`: 1-64 lowercase ASCII letters/digits and single internal hyphens; matches the folder.
- `description`: a non-empty string, at most 1024 characters; capability and routing context.
- Optional `license` and experimental `allowed-tools`: non-empty strings.
- Optional `compatibility`: a non-empty string, at most 500 characters.
- Optional `metadata`: string-key/string-value mapping. Quote versions and boolean-like strings.
- Unknown top-level fields are advisory warnings; strict policy rejects them.

Parsing uses PyYAML SafeLoader, supports quoted/folded/literal Unicode text and nested metadata,
rejects duplicate/non-string mapping keys and unsafe tags, and reports YAML locations.
PyYAML follows its YAML scalar rules: quote values such as `"true"`, `"on"` and `"1.0"` when
they must be strings. Merge overrides that create duplicate keys are rejected deliberately.
Generated frontmatter is serialized safely; description repair preserves metadata values, but
not original comments or formatting.

## Reviewed SkillPlan

Schema version remains 1. v0.8 adds optional fields; older plans load with empty defaults.

```json
{
  "schema_version": 1,
  "name": "csv-review",
  "description": "Use when checking CSV experiment data against its declared input contract before statistical analysis.",
  "brief": "Review the supplied CSV without changing it.",
  "workflow": [
    "Read references/contract.md and confirm the input columns.",
    "Report each contract violation with its original row and column."
  ],
  "quality_checks": ["The source file remains unchanged."],
  "resource_files": [
    {
      "path": "references/contract.md",
      "content": "# Contract\n\nID must be unique.\n",
      "purpose": "Read before checking the ID column."
    }
  ]
}
```

Existing fields (`resources`, `examples`, `constraints`, terminology, observed tools, failures,
sources and review notes) remain supported. Resources are written from complete content only;
their purposes are linked from the main instructions. Scripts are not executed by generation.

`resource_files` accepts objects with exactly `path`, `content`, `purpose`, all non-empty strings.
Paths use forward slashes under `references/`, `scripts/`, or `assets/`. Parent traversal,
absolute paths, Windows device names, duplicate case-insensitive file paths, file/directory
conflicts and symlink writes are rejected. `references/sources.md` is reserved for source-backed
plans. This protects writes; it is not a sandbox for later script execution.

Source-backed plans write a compact index of paths, kinds, hashes, sizes and observations, not
copies of source documents. Ingestion does not invent detailed procedures: review/add
`workflow` and `quality_checks` before publishing.

Manual workflow creation:

```bash
skill-factory generate --name csv-review --brief "Check the supplied CSV contract." \
  --description "Use when checking CSV experiment data against a declared contract before analysis." \
  --step "Confirm required and numeric columns." \
  --step "Report violations with original row numbers." \
  --check "Do not modify the input file."
```

Plans lacking concrete steps generate an explicit draft warning, promoted to an error by
strict policy. Valid structure alone does not imply useful or safe instructions.

## Codex Metadata

`agents/openai.yaml` places quoted UI strings under `interface`:

```yaml
interface:
  display_name: "CSV Review"
  short_description: "Check declared experimental CSV contracts"
  default_prompt: "Use $csv-review to complete the task with its documented workflow."
```

The generator keeps the UI blurb at 25-64 characters and includes `$skill-name` in the prompt.
No permissions or invocation-policy changes are inferred.

## Migration from v0.7

1. Install the v0.8 package so its PyYAML dependency is available.
2. Replace scaffold helpers/templates with real resources or remove them.
3. Add workflow/check fields to reviewed plans (or use manual steps/checks).
4. Re-run lint: valid optional fields now pass, but wrong YAML types and invalid lengths fail.
5. Re-generate Codex UI metadata or move existing UI keys under `interface`.
6. Review diffs before using `--force`; it is not a package-cleanup command.

Examples: [three practical Skills and a reviewed plan](../examples/README.md).
