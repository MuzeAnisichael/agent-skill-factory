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

Repair plans also require manual review for security-related lint findings. The default repair loop does not auto-apply destructive, exfiltration, or approval-bypass changes.

### Traceability

Store:

- Source material hashes.
- Generated files.
- Lint reports.
- Eval reports.
- Repair history.
- Approval records.

### Untrusted Ingestion

Document and trace ingestion is read-only and bounded by file-count and byte limits. The ingestion
layer rejects binary or non-UTF-8 input, stores hashes instead of copying full source files, and
omits lines matching known destructive, exfiltration, approval-bypass, or prompt-injection
patterns. Every omission is recorded in the reviewable `SkillPlan`.

These filters are heuristic. A source-backed Skill still requires human review, lint, and
task-specific evals before installation.

## Default Policy

The default generated Skill should be read-only unless the source task explicitly requires state changes.
