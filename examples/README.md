# Practical Examples / 实用示例

These examples target students and early-career research developers. They are maintained
packages, not generated placeholders. Read their workflows and resources before installation.

| Skill | Use / 用途 | Resources |
|---|---|---|
| [python-code-review](skills/python-code-review/SKILL.md) | Evidence-based Python review / Python 代码审查 | Focused checklist |
| [experiment-csv-check](skills/experiment-csv-check/SKILL.md) | Read-only CSV contract checks / 实验 CSV 质量检查 | Executable helper, contract, sample data |
| [experiment-report-check](skills/experiment-report-check/SKILL.md) | Report consistency review / 实验报告一致性审阅 | Checklist and usable review template |

From a source checkout after `python -m pip install -e .`:

```bash
skill-factory lint examples/skills/python-code-review examples/skills/experiment-csv-check examples/skills/experiment-report-check --policy strict
skill-factory eval examples/skills/experiment-csv-check
python examples/skills/experiment-csv-check/scripts/check_csv.py examples/skills/experiment-csv-check/assets/sample.csv --required id --numeric value --unique id
skill-factory generate --from-plan examples/plans/python-code-review.json --output out/skills
skill-factory lint out/skills/python-code-review --policy strict
```

Export a reviewed example to a project-local directory (this copies files, not a sandbox):

```bash
skill-factory export examples/skills/experiment-csv-check --target agent-skills --output .agents/skills
```

The JSON evals check package content and heuristic routing only. They do not execute the
review workflows or prove that an Agent improves. The CSV helper is separately executed
against clean, malformed, and contract-violating inputs in `tests/test_examples.py`.
No live model benchmark is claimed.

这些示例的 JSON 评测只检查包内容与启发式触发，不代表真实 Agent 的质量提升。
CSV 脚本另有真实执行测试；两种证据不能混为一谈。

The reviewed plan demonstrates the v0.8 additive fields `workflow`, `quality_checks`, and
`resource_files`. It generates a smaller review Skill, not a byte-identical copy of the
maintained example above. Edit and review plans before writing or executing model-produced code.

Examples ship in the repository and source archive. They are not included in the lightweight
runtime wheel; obtain them from the repository linked in the installed package metadata.
