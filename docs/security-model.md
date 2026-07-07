# Security Model

Agent Skill Factory treats Skills as executable influence over an Agent. A malicious or sloppy Skill can cause data leaks, unsafe tool calls, or persistent behavior changes.

## Threats

- Prompt injection through source documents or traces.
- Overbroad tool permissions.
- Hidden side effects in scripts.
- Exfiltration through network calls or generated messages.
- Unsafe shell commands.
- Skills that trigger too broadly.
- Untrusted project-level Skills.

## Controls

### Least Privilege

Generated Skills should not request tool permissions unless needed. High-risk tools should require explicit user approval.

### Sandboxed Evaluation

Eval runs should execute in an isolated workspace with synthetic data whenever possible.

### Static Risk Classification

Assign a risk level:

- Low: read-only guidance or formatting.
- Medium: local file writes or deterministic scripts.
- High: shell commands, network calls, external system changes.
- Critical: deployment, deletion, credential access, payment, production data changes.

### Human Approval

Require human approval for Skills that:

- Delete or overwrite files.
- Send messages externally.
- Deploy or modify infrastructure.
- Access secrets.
- Modify production systems.

### Traceability

Store:

- Source material hashes.
- Generated files.
- Lint reports.
- Eval reports.
- Repair history.
- Approval records.

## Default Policy

The default generated Skill should be read-only unless the source task explicitly requires state changes.
