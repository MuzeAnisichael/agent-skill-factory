# Lint Policies

`skill-factory lint` supports three built-in profiles:

| Profile | Description minimum | Body maximum | Warning behavior |
|---|---:|---:|---|
| `standard` | 60 characters | 500 lines | Warnings remain advisory |
| `strict` | 80 characters | 300 lines | Known warning codes fail lint |
| `permissive` | 40 characters | 800 lines | Warnings remain advisory |

Use a built-in profile:

```bash
skill-factory lint skills/example --policy strict
```

`--max-lines` overrides only the selected profile's body limit.

## Custom Policy

Custom policies are versioned JSON files and extend a built-in profile:

```json
{
  "schema_version": 1,
  "name": "research-lab",
  "extends": "strict",
  "max_lines": 350,
  "description_min_length": 80,
  "warnings_as_errors": [
    "frontmatter.description.short",
    "frontmatter.description.trigger_weak",
    "frontmatter.extra_keys"
  ]
}
```

```bash
skill-factory lint skills/example --policy-file policies/research-lab.json
```

Unknown fields, profiles, warning codes, and non-positive numeric limits are rejected. Security,
syntax, missing-resource, and structural errors always fail lint and cannot be downgraded by a
policy.

## Supported Warning Codes

- `body.generic_filler`
- `body.too_long`
- `body.trigger_in_body`
- `frontmatter.description.short`
- `frontmatter.description.trigger_weak`
- `frontmatter.extra_keys`
- `layout.auxiliary_doc`
