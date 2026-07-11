# Documentation

This directory documents the current behavior and design boundaries of Agent Skill Factory.

## Start Here

| Document | Purpose |
|---|---|
| [Architecture](architecture.md) | End-to-end flow, module responsibilities, and deployment shape. |
| [Development Plan](development-plan.md) | Product goal, non-goals, milestones, and current completion matrix. |
| [Roadmap](../ROADMAP.md) | Public milestone status and prioritized backlog. |
| [Security Model](security-model.md) | Threats, controls, trust boundaries, and default policy. |

## Build Skills

| Document | Purpose |
|---|---|
| [Source and Trace Ingestion](ingestion.md) | Build reviewable plans from files, directories, and Agent traces. |
| [Skill Output Format](skill-output-format.md) | Required package structure and content placement rules. |
| [LLM Providers](llm-providers.md) | Configure local Ollama or OpenAI-compatible APIs. |

## Validate and Distribute

| Document | Purpose |
|---|---|
| [Evaluation Strategy](evaluation.md) | Trigger, task, runner, and regression evaluation behavior. |
| [Repair Loop](repair.md) | Bounded automatic repairs, manual-review cases, and rollback rules. |
| [Registry and Export](registry.md) | Local metadata, quality gates, install, and export targets. |
| [Eval JSON Schema](eval-schema.json) | Machine-readable evaluation configuration contract. |
| [Trace JSON Schema](trace-schema.json) | Machine-readable Agent trace contract. |

## Project Policies

- [Contributing](../CONTRIBUTING.md)
- [Security Policy](../SECURITY.md)
- [Support](../SUPPORT.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [Changelog](../CHANGELOG.md)

Documentation describes released source behavior unless a section is explicitly marked as planned.
