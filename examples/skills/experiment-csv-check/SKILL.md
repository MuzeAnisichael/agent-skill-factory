---
name: experiment-csv-check
description: 用于在统计或绘图前检查实验 CSV 的列契约、缺失值、数值合法性和标识唯一性，当用户要求数据质量检查时输出行列证据，不擅自清洗或修改原始数据。
license: MIT
compatibility: Python 3.10+，标准库，无网络需求；CSV 使用 UTF-8，可含 BOM。
metadata:
  audience: students-and-researchers
  version: "1.0"
---

# Experiment CSV Check

## Workflow

1. 获取文件路径、分隔符与列契约。询问哪些列必填、哪些列必须是数值、哪些标识必须唯一；没有这些信息时只进行结构检查。
2. 阅读 `references/input-contract.md` 后选择检查参数。示例：`python scripts/check_csv.py assets/sample.csv --required id --numeric value --unique id`。
3. 运行只读检查脚本。返回码 0 表示所选契约通过，1 表示发现问题，2 表示文件、格式或参数无法检查。必要时用 `--delimiter` 指定单字符分隔符。
4. 解读 JSON 报告中的 `issue_count` 和 `issues`，引用行号、列名和错误类型，说明未声明的领域规则未被验证。问题展示最多 25 条，总数仍完整统计。
5. 对异常提出后续核查建议，不自动删行、插值、替换缺失值或写回原文件。

## Resources

- `scripts/check_csv.py`：只读、确定性的 CSV 契约检查。
- `references/input-contract.md`：输入约定、错误语义和边界。
- `assets/sample.csv`：最小可运行示例，用于验证本地环境。

## Quality Checks

- 原文件保持不变；报告能定位到原文件的行列。
- 不把未指定的缺失值、重复实验或统计离群点直接判成错误。
- 对 NaN/Infinity 和无法解析的指定数值列明确报告。
- 结构合法不等于实验有效，不声称已验证物理模型或统计结论。
