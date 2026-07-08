# Agent Skill Factory

<p align="right">
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a>
</p>

[![CI](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](ROADMAP.md)

Agent Skill Factory 是一个开源工具链，用于生成、校验和发布可复用的 Agent Skills。

它的目标是把真实任务、文档、代码库、工具说明和 Agent 运行 trace 转化为可复用、可评测、可发布的 Skill 包，而不是只生成一段长 prompt。

## 项目状态

项目目前处于早期 alpha 阶段。当前已经具备一个本地 Python CLI，可以初始化工作区、生成 Skill 草案、调用本地或 API 大模型进行结构化规划，对 Skill 质量和安全风险进行 lint 检查，并运行本地 eval。

| 模块 | 状态 | 说明 |
|---|---|---|
| 本地 CLI | 已完成 | 已实现 `init`、`generate` 和 `lint`。 |
| Skill 包写入器 | 已完成 | 可生成 `SKILL.md`、可选资源目录和 `agents/openai.yaml`。 |
| LLM 规划 | 已完成 | 支持本地 Ollama 和 OpenAI-compatible API，生成结构化 `SkillPlan`。 |
| 静态 Linter | 进行中 | 已覆盖命名、frontmatter、资源缺失、危险指令和 Python 脚本语法。 |
| Eval Runner | 进行中 | 已实现本地触发测试和任务断言测试；下一步是 Agent-backed baseline eval。 |
| Repair Loop | 计划中 | 根据 lint/eval 失败进行受控自动修复。 |
| Registry 和导出 | 计划中 | 本地注册表、版本元数据和安装适配器。 |

## 为什么做这个项目

Agent Skills 正在成为扩展 coding agent 和 workflow agent 的实用方式：它可以沉淀领域流程、工具用法、参考资料、脚本和模板。一个好的 Skill 应该简洁、边界清楚、可测试并且默认安全。一次性让大模型生成 `SKILL.md` 并不足以支撑生产使用。

Agent Skill Factory 关注完整生命周期：

```text
源材料 -> Skill 规划 -> Skill 生成 -> lint -> eval -> repair -> registry -> publish
```

## 范围

当前仓库从轻量但完整的架构开始，覆盖：

- 生成标准 Skill 包。
- 校验 `SKILL.md` 结构和触发质量。
- 使用本地 Ollama 或 OpenAI-compatible API 规划 Skill 包。
- 对比 with-skill 和 without-skill 的任务表现。
- 检测安全和权限风险。
- 在本地或托管 Skill Registry 中管理版本。
- 导出到兼容 Agent Skills 的客户端，例如 Codex、Claude Code 和 ADK 风格运行时。

## Skill 包目标结构

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
├── assets/
└── agents/openai.yaml
```

`SKILL.md` 只放高价值说明。长领域资料放入 `references/`，确定性操作放入 `scripts/`，可复用模板或静态资源放入 `assets/`。

## MVP 模块

1. Builder：从任务示例和源材料创建 Skill 草案。
2. Linter：检查命名、元数据、长度、缺失文件、空泛说明和危险权限。
3. Eval Runner：运行触发测试，以及 with-skill vs without-skill 任务对比。
4. Repair Agent：根据 lint 和 eval 失败进行受控修改。
5. Registry：保存 Skill 版本、评分、依赖、风险级别和导出目标。

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

不安装直接运行：

```bash
PYTHONPATH=src python -m skill_factory --version
PYTHONPATH=src python -m skill_factory lint skills/release-note-builder
```

运行测试：

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## 仓库结构

```text
src/skill_factory/       核心 CLI、生成器、linter、LLM provider 和数据模型
tests/                   CLI、规划、生成和 lint 的单元测试
docs/                    架构、LLM provider、评测、安全和格式文档
.github/                 CI、issue 模板和 PR 模板
ROADMAP.md               开发计划和完成度表
```

## 文档

- [Roadmap and Completion Table](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [Development Plan](docs/development-plan.md)
- [Skill Output Format](docs/skill-output-format.md)
- [LLM Providers](docs/llm-providers.md)
- [Evaluation Strategy](docs/evaluation.md)
- [Security Model](docs/security-model.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

## 当前 CLI

```bash
skill-factory --help
skill-factory init ./workspace
skill-factory plan --provider ollama --model llama3.1 --brief "Create a Skill for release notes."
skill-factory generate --name "Release Note Builder" --brief "Create release notes." --output skills
skill-factory generate --llm --provider ollama --model llama3.1 --brief "Create release notes." --output skills
skill-factory lint skills/release-note-builder
skill-factory eval skills/release-note-builder # 添加 evals/evals.json 后运行
```

生成的 Skill 目标结构保持简单，并兼容 Agent Skills 风格客户端：

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
├── assets/
└── agents/openai.yaml
```

## 贡献

欢迎以小而清晰的变更参与贡献。适合优先参与的方向包括 lint 规则、fixture Skills、eval 文件格式、CLI 易用性和文档示例。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 安全

生成的 Skills 会影响 Agent 行为和工具使用。在完成 lint 和评测前，应将所有生成 Skill 视为不可信。详见 [SECURITY.md](SECURITY.md) 和 [Security Model](docs/security-model.md)。

## License

MIT
