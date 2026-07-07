# Skill Output Format

The project targets the Agent Skills folder format.

## Required Structure

```text
skill-name/
└── SKILL.md
```

The folder name and frontmatter `name` should match.

## Recommended Structure

```text
skill-name/
├── SKILL.md
├── references/
│   └── domain.md
├── scripts/
│   └── helper.py
├── assets/
│   └── template.md
└── agents/
    └── openai.yaml
```

## SKILL.md Rules

Frontmatter:

```yaml
---
name: example-skill
description: Use this skill when the agent needs to ...
---
```

Body:

- Use direct instructions.
- Prefer concise examples over long explanations.
- State defaults clearly.
- Link to supporting files only when needed.
- Keep detailed domain material out of the main body.

## Resource Placement

Use `references/` for:

- API docs.
- Schemas.
- Business rules.
- Long examples.
- Domain-specific playbooks.

Use `scripts/` for:

- Deterministic transformations.
- Repeated file operations.
- Validation utilities.
- Data extraction.

Use `assets/` for:

- Templates.
- Images.
- Example files.
- Static boilerplate.

## Avoid

- Extra README files inside each Skill.
- Generic best-practice essays.
- Duplicating reference content in `SKILL.md`.
- Deeply nested resource chains.
- Broad tool permissions.
- Hidden side effects.
