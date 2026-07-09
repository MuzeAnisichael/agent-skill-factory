# Agent Skill Factory

<p align="right">
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a>
</p>

[![CI](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](ROADMAP.md)

Agent Skill Factory 是一个开源的本地工具链，用于生成、校验、评测、注册和导出可复用的 Agent Skills。

它的目标是把真实任务说明、文档、代码库规范、工具描述以及未来的 Agent trace 转化为可测试的 Skill 包，而不是只生成一段很长的 prompt。

## 项目状态

当前版本：`0.4.0`

项目仍处于 alpha 阶段，但本地生命周期已经可以端到端使用：

| 模块 | 状态 | 说明 |
|---|---|---|
| 本地 CLI | 已完成 | 支持 `init`、`plan`、`generate`、`lint`、`eval`、`registry`、`export`、`install` 和 `eval-schema`。 |
| Skill 包写入器 | 已完成 | 生成 `SKILL.md`、可选资源目录和 `agents/openai.yaml`。 |
| LLM 规划 | 已完成 | 支持本地 Ollama 和 OpenAI-compatible API，输出结构化 `SkillPlan`。 |
| 静态 linter | 进行中 | 覆盖命名、frontmatter、资源缺失、危险指令和 Python 脚本语法。 |
| Eval runner | 进行中 | 已支持本地触发测试、任务断言、runner-backed eval、Markdown/JSON 报告和回归对比。 |
| 本地注册表和导出 | 已完成 | 文件型 registry、源码哈希、风险摘要、eval 状态和客户端目录导出。 |
| Runner 抽象 | 已完成 | 支持确定性的 dry-run runner，以及可选的 Ollama/OpenAI-compatible LLM runner。 |
| Repair loop | 计划中 | 基于 lint/eval 失败进行受控修复。 |
| Agent-backed eval | 计划中 | 后续接入真实 Agent runtime、工具调用和 trace。 |

## 为什么做这个项目

Agent Skills 正在成为扩展 coding agent 和 workflow agent 的实用方式。一个好的 Skill 可以沉淀领域流程、参考资料、脚本、工具用法和模板。面向生产使用时，Skill 应该边界清晰、内容简洁、可测试，并且默认安全。一次性让大模型生成 `SKILL.md` 不足以支撑可靠使用。

Agent Skill Factory 关注完整的本地生命周期：

```text
源材料 -> Skill 规划 -> Skill 生成 -> lint -> eval -> registry -> export/install
```

## Skill 包目标结构

```text
skill-name/
|-- SKILL.md
|-- references/
|-- scripts/
|-- assets/
`-- agents/openai.yaml
```

`SKILL.md` 只放高价值指令。较长的领域材料放入 `references/`，确定性操作放入 `scripts/`，可复用模板或静态资源放入 `assets/`。

## 快速开始

环境要求：

- Python 3.10+
- Git

从源码运行：

```bash
python -m pip install -e .
skill-factory init .
skill-factory generate \
  --name "Release Note Builder" \
  --description "Use this skill when the agent needs to create release notes from repository changes." \
  --brief "Create concise release notes grounded in repository changes." \
  --resources references,scripts \
  --output skills
skill-factory lint skills/release-note-builder
```

添加 `evals/evals.json` 后运行本地评测：

```bash
skill-factory eval skills/release-note-builder
skill-factory eval skills/release-note-builder --json
skill-factory eval skills/release-note-builder --markdown-output eval-report.md
skill-factory eval skills/release-note-builder --baseline-skill old-skills/release-note-builder
skill-factory eval-schema --output docs/eval-schema.json
```

使用确定性的 dry-run runner 运行 runner-backed eval，或显式启用 LLM runner：

```bash
skill-factory eval skills/release-note-builder --runner dry-run
skill-factory eval skills/release-note-builder \
  --runner llm \
  --provider ollama \
  --model llama3.1
```

注册并安装 Skill：

```bash
skill-factory registry add skills/release-note-builder --version 0.1.0
skill-factory registry list
skill-factory install release-note-builder --target agent-skills
```

不经过注册表，直接导出：

```bash
skill-factory export skills/release-note-builder --target codex --output .codex/skills
skill-factory export skills/release-note-builder --target claude-code --output .claude/skills
```

使用本地 Ollama 模型规划并生成：

```bash
skill-factory plan \
  --provider ollama \
  --model llama3.1 \
  --brief "Create a Skill for turning merged pull requests into release notes."

skill-factory generate \
  --llm \
  --provider ollama \
  --model llama3.1 \
  --brief "Create a Skill for turning merged pull requests into release notes." \
  --resources references,scripts \
  --output skills
```

使用 OpenAI-compatible API：

```bash
skill-factory plan \
  --provider openai-compatible \
  --api-base https://api.openai.com/v1 \
  --api-key "$OPENAI_API_KEY" \
  --model "$OPENAI_MODEL" \
  --brief "Create a Skill for reviewing Terraform changes."
```

不安装包，直接从源码运行：

```bash
PYTHONPATH=src python -m skill_factory --version
PYTHONPATH=src python -m skill_factory lint skills/release-note-builder
PYTHONPATH=src python -m skill_factory registry list
```

运行测试：

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## 仓库结构

```text
src/skill_factory/       核心 CLI、生成器、linter、evaluator、runner、registry、schemas 和 LLM providers
tests/                   CLI、规划、生成、lint、eval、runner、registry 和 schema 的单元测试
docs/                    架构、LLM provider、评测、注册表、安全和格式文档
.github/                 CI、issue 模板和 PR 模板
ROADMAP.md               开发计划和完成表
```

## 文档

- [路线图和完成表](ROADMAP.md)
- [架构](docs/architecture.md)
- [开发计划](docs/development-plan.md)
- [Skill 输出格式](docs/skill-output-format.md)
- [LLM Providers](docs/llm-providers.md)
- [评测策略](docs/evaluation.md)
- [Eval JSON Schema](docs/eval-schema.json)
- [注册表和导出](docs/registry.md)
- [安全模型](docs/security-model.md)
- [贡献指南](CONTRIBUTING.md)
- [安全政策](SECURITY.md)

## 安全

生成或导入的 Skills 会影响 Agent 行为和工具使用。在通过 lint 和 eval 之前，应将其视为不可信内容。详见 [SECURITY.md](SECURITY.md) 和 [Security Model](docs/security-model.md)。

## License

MIT
