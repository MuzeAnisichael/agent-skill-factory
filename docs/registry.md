# Registry and Export

`v0.3.0` adds a local file-based registry so generated Skills can be tracked, reviewed, and installed into Agent client directories.

The registry is intentionally simple. It is a JSON file, not a database or service.

Default path:

```text
.skill-factory/registry.json
```

## Commands

Add or update an entry:

```bash
skill-factory registry add skills/release-note-builder --version 0.1.0
```

List entries:

```bash
skill-factory registry list
skill-factory registry list --json
```

Show one entry:

```bash
skill-factory registry show release-note-builder
skill-factory registry show release-note-builder --json
```

Install a registered Skill:

```bash
skill-factory install release-note-builder --target agent-skills
skill-factory install release-note-builder --target codex --output .codex/skills
skill-factory install release-note-builder --target claude-code --output .claude/skills
```

Export a Skill directly without registering it:

```bash
skill-factory export skills/release-note-builder --target agent-skills
skill-factory export skills/release-note-builder --target codex --output .codex/skills
```

Use `--force` to overwrite an existing exported copy.

## Registry Entry Shape

```json
{
  "schema_version": 1,
  "skills": {
    "release-note-builder": {
      "name": "release-note-builder",
      "description": "Use this skill when the agent needs to create release notes from repository changes.",
      "version": "0.1.0",
      "path": "skills/release-note-builder",
      "risk": {
        "level": "low",
        "lint_errors": 0,
        "lint_warnings": 0
      },
      "eval": {
        "status": "missing"
      },
      "source": {
        "package_sha256": "64 hex characters",
        "files": [
          {
            "path": "SKILL.md",
            "sha256": "64 hex characters"
          }
        ]
      },
      "export_targets": []
    }
  }
}
```

## Quality Gate

`registry add` runs lint before writing the entry.

Default behavior:

- Lint errors block registration.
- Existing evals are run when `<skill>/evals/evals.json` exists.
- Failing or invalid evals block registration.
- Missing evals are recorded as `"status": "missing"` and do not block registration.

Override behavior:

```bash
skill-factory registry add skills/example --allow-failing
skill-factory registry add skills/example --skip-eval
```

`--allow-failing` is intended for explicit review workflows. Do not use it for release candidates.

## Risk Summary

Risk is derived from lint results:

| Level | Meaning |
|---|---|
| `high` | Security-related lint error was found. |
| `medium` | Non-security lint error was found. |
| `low` | No lint errors. Warnings may still be present. |

## Export Targets

Supported targets:

| Target | Default destination |
|---|---|
| `agent-skills` | `.agents/skills/` |
| `codex` | `.codex/skills/` |
| `claude-code` | `.claude/skills/` |

All current targets use the same core package layout: a directory containing `SKILL.md` and optional `references/`, `scripts/`, `assets/`, and `agents/` files.

## Design Notes

- Registry data is deterministic and reviewable in git.
- Source hashes are calculated from sorted package files.
- Runtime dependencies remain zero.
- The registry stores metadata only; the source Skill directory remains the source of truth.
- Hosted registries, signing, dependency resolution, and trust policies are future work.
