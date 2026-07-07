# Architecture

Agent Skill Factory is designed as a small set of composable services. The architecture should stay simple enough for local CLI use while leaving a path to a hosted web app.

## System Flow

```mermaid
flowchart LR
  A["Task examples / docs / code / traces"] --> B["Ingestion"]
  B --> C["Skill Planner"]
  C --> D["Skill Generator"]
  D --> E["Static Linter"]
  E --> F["Eval Runner"]
  F --> G["Repair Agent"]
  G --> D
  F --> H["Skill Registry"]
  H --> I["Export / Install"]
  J["MCP and Tool Catalog"] --> C
  J --> D
```

## Modules

### 1. Ingestion

Normalizes source material into structured inputs:

- User-provided task examples.
- Existing SOPs, API docs, schemas, code conventions, and templates.
- Agent traces from successful or failed task runs.
- Tool descriptions from local functions, OpenAPI specs, or MCP servers.

Output:

```json
{
  "task_examples": [],
  "source_documents": [],
  "tool_candidates": [],
  "constraints": [],
  "failure_cases": []
}
```

### 2. Skill Planner

Classifies the Skill before generation:

- Knowledge Skill: domain rules, policies, vocabulary, style guides.
- Workflow Skill: multi-step procedures and decision points.
- Tool Skill: instructions for using APIs, MCP tools, or scripts.
- Asset Skill: reusable templates and static resources.
- Hybrid Skill: `SKILL.md` plus references, scripts, and assets.

The planner decides the target resources and how much freedom the Agent should have:

- High freedom: heuristic guidance for flexible work.
- Medium freedom: preferred patterns and pseudocode.
- Low freedom: exact scripts or command sequences for fragile operations.

### 3. Skill Generator

Creates the Skill package:

- `SKILL.md`
- optional `references/`
- optional `scripts/`
- optional `assets/`
- optional `agents/openai.yaml`

Generation rules:

- Put triggering information in the frontmatter description.
- Keep `SKILL.md` concise.
- Move long domain content into `references/`.
- Add scripts when deterministic reliability matters.
- Do not add auxiliary docs inside the generated Skill package.

### 4. Static Linter

Checks basic correctness before any Agent run:

- Folder name matches Skill name.
- Name uses lowercase letters, digits, and hyphens.
- Description explains both capability and trigger context.
- `SKILL.md` stays below configured line/token limits.
- Referenced files exist.
- Scripts declare dependencies and fail clearly.
- Instructions are not generic filler.
- Dangerous permissions are flagged.

### 5. Eval Runner

Runs isolated comparisons:

- Trigger eval: should-trigger vs should-not-trigger prompts.
- Output eval: realistic task cases with expected outcomes.
- Baseline eval: with-skill vs without-skill or old-skill vs new-skill.
- Cost eval: token count, runtime, and tool-call count.
- Safety eval: attempts to trigger unsafe actions or data exposure.

### 6. Repair Agent

Turns lint and eval failures into bounded edits:

- Change the description.
- Remove redundant instructions.
- Add a missing edge case.
- Split long content into references.
- Add or harden a script.
- Narrow permissions.

The repair loop should reject edits that do not improve held-out eval scores.

### 7. Skill Registry

Stores generated Skills and metadata:

```json
{
  "name": "example-skill",
  "version": "0.1.0",
  "status": "draft",
  "risk_level": "low",
  "eval_score": 0.0,
  "source_hashes": [],
  "export_targets": ["agents", "claude", "codex"]
}
```

## Deployment Shape

Phase 1 should be a local CLI. Later phases can add:

- Web UI for uploading source material and reviewing generated Skills.
- Hosted registry with signed Skill packages.
- MCP integration for tool discovery.
- Multi-agent eval execution.
