# Agent Skill Factory

<p align="right">
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">简体中文</a>
</p>

[![CI](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/MuzeAnisichael/agent-skill-factory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.8.0-1769aa.svg)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](ROADMAP.md)

Agent Skill Factory 是一个开源的本地工具链，用于生成、校验、评测、注册和导出可复用的 Agent Skills。

它的目标是把真实任务说明、文档、代码库规范、工具描述以及 Agent trace 转化为可测试的 Skill 包，而不是只生成一段很长的 prompt。

```text
来源与 trace -> 可审阅计划 -> Skill 包 -> lint/eval -> repair -> registry -> export
```

**本地优先、计划可审阅、仅有一个小型运行依赖 PyYAML。** LLM 是可选能力：可以使用本地 Ollama、OpenAI-compatible API，也可以完全离线使用。`plan` + `generate --from-plan` 支持先审阅后写入；`generate --llm` 会直接写入，需在生成后审阅。

## 项目状态

当前版本：`0.8.0`

项目仍处于 alpha 阶段，但本地生命周期已经可以端到端使用。
下表状态描述本地实现，不代表真实场景中的 Agent 效果已经验证：

| 模块 | 状态 | 说明 |
|---|---|---|
| 本地 CLI | 已完成 | 支持 `init`、`ingest`、`plan`、`generate`、`lint`、`eval-generate`、`eval`、`repair`、provider health、注册/导出/安装和 schema 命令。 |
| Skill 包写入器 | 已集成验证 | 写入具体工作流、验收检查与完整资源；不完整流程标记为草稿，并生成 Codex interface 元数据。 |
| LLM 规划 | 已完成 | 支持本地 Ollama 和 OpenAI-compatible API，输出结构化 `SkillPlan`。 |
| 来源/Trace 摄取 | 已完成 | 从 UTF-8 文件、目录以及成功或失败的 Agent trace 确定性生成计划。 |
| 静态 linter | 已实现 | 安全 YAML、标准可选字段、元数据类型、中英文触发提示及可配置策略。 |
| Eval runner | 进行中 | 来源感知草案、触发/任务/runner 评测、报告和回归对比。 |
| 本地注册表和导出 | 已完成 | 文件型 registry、源码哈希、风险摘要、eval 状态和客户端目录导出。 |
| Runner 抽象 | 已完成 | 支持 dry-run、可选 LLM 和 JSON subprocess Agent runner。 |
| Repair loop | 已完成 | 支持受控修复计划、安全确定性编辑、重跑 lint/eval，并在回归时回滚。 |
| Agent-backed eval | 进行中 | 已有通用 subprocess adapter；仍需专用 runtime adapter 和自动 trace 采集。 |

测试覆盖本地生命周期、YAML 兼容、可审阅计划与可执行示例。CI 在 Linux/Windows 上测试 Python 3.10-3.12，并分别构建、安装源码包和 wheel。[v0.8 验证记录](docs/releases/v0.8.0.md)给出结果与限制。

v0.8 聚焦内容实用性和格式兼容；[v0.9](ROADMAP.md#v09-real-agent-evidence)验证真实 Agent 任务效果，v0.10 完善可信分发。[三个实用示例](examples/README.md)覆盖 Python 作业审查、实验 CSV 检查和实验报告一致性审阅。

**评测边界：** 关键词、包文本与 dry-run 得分不证明 Agent 能力提升。目前没有专用 Agent adapter、执行沙箱或独立的生成质量基准。

## 项目范围和边界

Agent Skill Factory 是 Skill 生命周期的精简无界面核心。它既可以直接通过 CLI 使用，也可以作为未来桌面端、Web、课程或实验室工作区的底层模块。

当前已经包含：

- 确定性和 LLM 辅助的 `SkillPlan` 创建
- 带来源记录的本地资料与 Agent trace 摄取
- Skill 包生成、lint、eval 和受控 repair
- 可配置 lint 策略和来源感知 eval 草案生成
- 本地 registry 元数据、导出和安装
- 本地 Ollama 和 OpenAI-compatible 模型 provider
- 用于外部 Agent eval runner 的显式 subprocess 协议

当前尚未实现：

- 图形界面或托管服务
- 专用 Agent adapter、runtime 隔离和自动 trace 采集
- 多用户工作区、审核流程或云同步
- 包签名、能力权限或公共市场

这些边界是有意保留的。未来托管协作层应复用同一套经过测试的核心，而不是重复实现校验和安全规则。

## 为什么做这个项目

Agent Skills 正在成为扩展 coding agent 和 workflow agent 的实用方式。一个好的 Skill 可以沉淀领域流程、参考资料、脚本、工具用法和模板。面向生产使用时，Skill 应该边界清晰、内容简洁、可测试，并且默认安全。一次性让大模型生成 `SKILL.md` 不足以支撑可靠使用。

Agent Skill Factory 关注完整的本地生命周期：

```text
源材料 -> 摄取/规划 -> 人工审阅 -> Skill 生成 -> lint -> eval -> registry -> export/install
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

从源码安装：

```bash
python -m pip install -e .
skill-factory init .
skill-factory generate \
  --name "Release Note Builder" \
  --description "Use this skill when the agent needs to create release notes from repository changes." \
  --brief "Create concise release notes grounded in repository changes." \
  --step "Collect reviewed changes and retain their source identifiers." \
  --step "Group user-visible changes and note breaking changes separately." \
  --check "Every release item is supported by a reviewed source change." \
  --output skills
skill-factory lint skills/release-note-builder
```

以上命令根据明确步骤创建包，再进行本地检查。`--resources` 仅创建目录；完整资源内容应放入可审阅计划。生成过程不会执行脚本。

也可以从完整示例开始：

```bash
skill-factory generate --from-plan examples/plans/python-code-review.json --output skills
skill-factory lint skills/python-code-review --policy strict
python examples/skills/experiment-csv-check/scripts/check_csv.py examples/skills/experiment-csv-check/assets/sample.csv --required id --numeric value --unique id
```

示例包含在仓库和源码包中，不包含在精简运行 wheel 中。构建产物可从 [GitHub Releases](https://github.com/MuzeAnisichael/agent-skill-factory/releases) 获取；本次不发布到 PyPI。

从本地文档、代码和 Agent trace 创建可审阅计划，再据此生成 Skill：

```bash
skill-factory ingest docs src/example.py \
  --trace traces/release.trace.json \
  --name "Release Note Builder" \
  --output skill-plan.json
```

审阅计划并补充具体的 `workflow` 和 `quality_checks`，再执行：

```bash
skill-factory generate --from-plan skill-plan.json --output skills
skill-factory eval-generate \
  --from-plan skill-plan.json \
  --output skills/release-note-builder/evals/evals.json
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

启用更严格的内置 lint 策略，或使用版本化的团队策略：

```bash
skill-factory lint skills/release-note-builder --policy strict
skill-factory lint skills/release-note-builder --policy-file policies/team.json
```

使用确定性的 dry-run runner 运行 runner-backed eval，或显式启用 LLM runner：

```bash
skill-factory eval skills/release-note-builder --runner dry-run
skill-factory eval skills/release-note-builder \
  --runner llm \
  --provider ollama \
  --model llama3.1
skill-factory eval skills/release-note-builder \
  --runner subprocess \
  --runner-command '["python","adapters/my_agent.py"]'
```

规划并应用受控修复：

```bash
skill-factory repair plan skills/release-note-builder
skill-factory repair plan skills/release-note-builder --json
skill-factory repair apply skills/release-note-builder
```

Repair 可以修复弱 description、缺失引用资源、过长 `SKILL.md` 正文，以及缺失的正向 eval 断言。安全相关发现会标记为人工审查，不会自动应用。

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
skill-factory provider-health --provider ollama --model llama3.1

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

不安装本项目而直接运行源码时，需先安装 `PyYAML>=6.0.2,<7`。在 macOS 或 Linux 上：

```bash
PYTHONPATH=src python -m skill_factory --version
PYTHONPATH=src python -m skill_factory lint skills/release-note-builder
PYTHONPATH=src python -m skill_factory registry list
```

在 PowerShell 中直接从源码运行（需已安装 PyYAML）：

```powershell
$env:PYTHONPATH = "src"
python -m skill_factory --version
python -m skill_factory lint skills/release-note-builder
python -m skill_factory registry list
```

从源码目录运行测试：

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## 仓库结构

```text
src/skill_factory/       核心 CLI、摄取、规划、生成、lint/eval/repair、registry、schemas 和 LLM providers
tests/                   覆盖本地生命周期的单元测试和离线 fixtures
examples/                三个维护中的完整 Skill 和可审阅生成计划
tools/check_package.py   干净环境中验证源码包/wheel 安装及 CLI 生命周期
docs/                    架构、摄取、LLM provider、评测、注册表、安全和格式文档
.github/                 CI、issue 模板和 PR 模板
docs/README.md           按工作流组织的文档入口
ROADMAP.md               开发计划和完成表
```

## 文档

- [文档索引](docs/README.md)
- [路线图和完成表](ROADMAP.md)
- [架构](docs/architecture.md)
- [开发计划](docs/development-plan.md)
- [来源与 Trace 摄取](docs/ingestion.md)
- [Skill 输出格式](docs/skill-output-format.md)
- [实用示例](examples/README.md)
- [v0.8 验证与迁移](docs/releases/v0.8.0.md)
- [LLM Providers](docs/llm-providers.md)
- [Lint 策略](docs/lint-policies.md)
- [评测策略](docs/evaluation.md)
- [Runner Adapter](docs/runner-adapters.md)
- [Repair Loop](docs/repair.md)
- [Eval JSON Schema](docs/eval-schema.json)
- [Trace JSON Schema](docs/trace-schema.json)
- [注册表和导出](docs/registry.md)
- [安全模型](docs/security-model.md)
- [贡献指南](CONTRIBUTING.md)
- [安全政策](SECURITY.md)

## 贡献和支持

贡献应保持核心精简，在可行时优先使用确定性实现，并确保文件或工具操作可以在执行前审阅。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和[路线图](ROADMAP.md)，再通过仓库 Issue 模板提交可复现的问题或范围清晰的功能建议。

使用问题请参考 [SUPPORT.md](SUPPORT.md)。安全漏洞请按照 [SECURITY.md](SECURITY.md) 中的流程私下报告。

## 安全

生成或导入的 Skills 会影响 Agent 行为和工具使用。使用前应审阅指令与代码；lint 和 eval 只是部分检查，不是可信保证或执行沙箱。详见 [SECURITY.md](SECURITY.md) 和 [Security Model](docs/security-model.md)。

## License

MIT
