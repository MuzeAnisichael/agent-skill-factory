# Runner Adapters

The `subprocess` eval runner is the first boundary for integrating a real Agent runtime without
adding that runtime as a package dependency. It starts only when explicitly selected, uses
`shell=False`, and applies a timeout.

```bash
skill-factory eval skills/example \
  --runner subprocess \
  --runner-command '["python","adapters/my_agent.py"]' \
  --runner-timeout 90
```

The command is a JSON string array, not a shell command. This preserves argument boundaries across
platforms and prevents shell expansion.

## Request Contract

Each runner test starts the adapter twice. JSON is supplied on standard input:

```json
{
  "schema_version": 1,
  "prompt": "Complete the task.",
  "use_skill": true,
  "skill": {
    "name": "example",
    "description": "Use this skill when ...",
    "body": "# Example\n...",
    "text": "name, description, and body",
    "path": "/path/to/example"
  }
}
```

When `use_skill` is false, `skill` is `null`. The adapter should run the requested Agent with or
without that context rather than simulating the difference itself.

## Response Contract

The process must exit with code zero and write one JSON object to standard output:

```json
{
  "output": "Agent result text",
  "metadata": {
    "runtime": "example-agent",
    "model": "example-model"
  }
}
```

`output` is required. `metadata` is optional. Invalid JSON, non-zero exit codes, timeouts, and
responses over 1 MB fail the runner case. Adapter logs belong on standard error; avoid secrets in
both output streams because error excerpts can appear in eval reports.

## Trust Boundary

The adapter command is trusted executable code with the permissions of the current user. Agent
Skill Factory does not sandbox it or approve its tool calls. Use a dedicated adapter process or
container when evaluating untrusted Skills, and keep destructive or external side effects disabled
by default.
