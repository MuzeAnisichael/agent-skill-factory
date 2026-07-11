# Contributing

Thanks for considering a contribution.

## Local Setup

Use Python 3.10 or newer.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

An editable install is the simplest cross-platform setup. To run directly from a checkout without installing, set `PYTHONPATH=src` on macOS/Linux or `$env:PYTHONPATH = "src"` in PowerShell before invoking Python.

The project currently has no runtime dependencies. Keep it that way unless a dependency removes meaningful complexity.

Before opening a pull request, run:

```bash
python -m compileall -q src
python -m unittest discover -s tests -v
```

GitHub Actions runs these checks on Python 3.10-3.12 on Linux and Windows.

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
- Source and trace ingestion extractors.
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
- Deterministic ingestion output and source-attribution behavior.
- Clarity of user-facing error messages.
