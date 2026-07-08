---
name: release-note-builder
description: Use this skill when the agent needs to create release notes from repository changes, merged pull requests, or changelog source material.
---

# Release Note Builder

## Objective

Create concise release notes grounded in repository changes and merged pull requests.

## Workflow

1. Inspect the provided change sources.
2. Group changes into features, fixes, documentation, and risks.
3. Cite concrete pull requests, commits, or files when available.
4. Avoid inventing unrelated work.

## Resources

- Load `references/domain.md` when release note style details are needed.

## Quality Bar

- Include a features section when feature changes exist.
- Include a fixes section when bug fixes exist.
- Call out migration risks or breaking changes.
