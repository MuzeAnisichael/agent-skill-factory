# Contributing

Thanks for considering a contribution.

## Development Principles

- Keep the system small and auditable.
- Prefer file-based workflows before adding infrastructure.
- Add tests for validation and safety rules.
- Treat generated Skills as potentially unsafe until linted and evaluated.
- Avoid vendor lock-in in the core Skill format.

## Contribution Areas

- Skill package generation.
- Static lint rules.
- Eval runners.
- Repair-loop strategies.
- Export adapters.
- Documentation and examples.

## Pull Request Checklist

- The change is scoped and documented.
- New behavior has tests or fixtures.
- Security implications are described.
- Generated examples do not include real secrets or private data.
