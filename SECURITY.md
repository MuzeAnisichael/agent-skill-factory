# Security Policy

Please report security issues privately before public disclosure.

## Supported Versions

This project is in alpha. Security fixes target the latest release and `main`; older alpha
versions do not have separate maintenance branches. Upgrade to the latest release when fixes ship.

## In Scope

- Unsafe generated Skill behavior.
- Permission escalation through Skill metadata.
- Secret exposure in generated files or eval reports.
- Unsafe script generation.
- Registry tampering or package substitution.

## Reporting

Open a private security advisory if available, or contact the maintainers through the repository owner.

Do not include real credentials, private customer data, or exploit payloads in public issues.

## Safe Disclosure Expectations

- Provide a minimal reproduction when possible.
- Use synthetic test data.
- Do not publish exploit details until maintainers have had time to respond.
- Avoid running untrusted generated Skills against production systems.
