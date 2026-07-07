# Contributing

Thanks for considering a contribution.

## Local Setup

Use Python 3.10 or newer.

```bash
python -m pip install -e .
PYTHONPATH=src python -m unittest discover -s tests
```

The project currently has no runtime dependencies. Keep it that way unless a dependency removes meaningful complexity.

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

## Branch and Commit Style

- Use small branches focused on one capability.
- Prefer clear imperative commit messages, such as `Add trigger eval schema`.
- Include tests or fixtures for behavior changes.
- Keep generated files out of commits unless they are deliberate examples.

## Pull Request Checklist

- The change is scoped and documented.
- New behavior has tests or fixtures.
- Security implications are described.
- Generated examples do not include real secrets or private data.

## Review Expectations

Maintainers should review for:

- Correctness of Skill format behavior.
- Risk of unsafe generated instructions.
- Regressions in CLI output.
- Cross-platform path handling.
- Clarity of user-facing error messages.
