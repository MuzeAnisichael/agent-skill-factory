# LLM Providers

Agent Skill Factory supports LLM-assisted planning without letting the model write files directly.

The LLM returns a structured `SkillPlan` JSON object:

```json
{
  "name": "release-note-builder",
  "description": "Use this skill when ...",
  "brief": "Create release notes from merged pull requests.",
  "resources": ["references", "scripts"],
  "examples": ["Create release notes for this branch."]
}
```

The deterministic generator then writes the Skill package from that plan.

## Local Ollama

Default provider:

```bash
skill-factory plan \
  --provider ollama \
  --model llama3.1 \
  --brief "Create a Skill for turning merged pull requests into release notes."
```

Generate files from an Ollama-planned Skill:

```bash
skill-factory generate \
  --llm \
  --provider ollama \
  --model llama3.1 \
  --brief "Create a Skill for turning merged pull requests into release notes." \
  --output skills
```

Environment variables:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

The Ollama provider calls:

```text
POST /api/chat
```

## OpenAI-Compatible API

Use this for OpenAI or compatible gateways:

```bash
skill-factory plan \
  --provider openai-compatible \
  --api-base https://api.openai.com/v1 \
  --api-key "$OPENAI_API_KEY" \
  --model "$OPENAI_MODEL" \
  --brief "Create a Skill for reviewing Terraform changes."
```

Environment variables:

```bash
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

The OpenAI-compatible provider calls:

```text
POST /v1/chat/completions
```

## Design Rules

- LLMs create plans, not files.
- CLI arguments override LLM plan fields.
- `resources` is restricted to `references`, `scripts`, and `assets`.
- Generated packages should still be linted before use.
- Future eval and repair steps should compare LLM-planned Skills against deterministic baselines.
