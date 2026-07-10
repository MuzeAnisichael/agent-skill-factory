from __future__ import annotations

from pathlib import Path

from .models import SkillPlan
from .naming import display_name, normalize_skill_name

RESOURCE_DIRS = {"references", "scripts", "assets"}


def create_skill(plan: SkillPlan, output_dir: Path, force: bool = False) -> Path:
    skill_name = normalize_skill_name(plan.name)
    skill_dir = output_dir / skill_name
    if skill_dir.exists() and not force:
        raise FileExistsError(f"skill already exists: {skill_dir}")

    skill_dir.mkdir(parents=True, exist_ok=True)
    selected_resources = tuple(resource for resource in plan.resources if resource in RESOURCE_DIRS)
    if plan.sources and "references" not in selected_resources:
        selected_resources = (*selected_resources, "references")
    for resource in selected_resources:
        (skill_dir / resource).mkdir(exist_ok=True)

    agents_dir = skill_dir / "agents"
    agents_dir.mkdir(exist_ok=True)

    (skill_dir / "SKILL.md").write_text(_render_skill_md(plan, selected_resources), encoding="utf-8")
    (agents_dir / "openai.yaml").write_text(_render_openai_yaml(plan), encoding="utf-8")

    if "references" in selected_resources:
        if plan.sources:
            (skill_dir / "references" / "sources.md").write_text(
                _render_source_index(plan), encoding="utf-8"
            )
        else:
            (skill_dir / "references" / "domain.md").write_text(
                _render_reference(plan), encoding="utf-8"
            )
    if "scripts" in selected_resources:
        (skill_dir / "scripts" / "helper.py").write_text(_render_helper_script(), encoding="utf-8")
    if "assets" in selected_resources:
        (skill_dir / "assets" / "template.md").write_text(_render_asset_template(plan), encoding="utf-8")

    return skill_dir


def _render_skill_md(plan: SkillPlan, resources: tuple[str, ...]) -> str:
    skill_name = normalize_skill_name(plan.name)
    description = plan.description.strip() or f"Use this skill when the agent needs to perform {skill_name} work."
    brief = plan.brief.strip() or "Add concrete workflow details before publishing this Skill."

    resource_lines: list[str] = []
    if "references" in resources and plan.sources:
        resource_lines.append(
            "- Load `references/sources.md` when source provenance, terminology, observed tools, "
            "or failure cases are needed."
        )
    elif "references" in resources:
        resource_lines.append("- Load `references/domain.md` only when domain details are needed.")
    if "scripts" in resources:
        resource_lines.append("- Prefer `scripts/helper.py` for deterministic repeated operations.")
    if "assets" in resources:
        resource_lines.append("- Use files under `assets/` as output templates or static resources.")
    if not resource_lines:
        resource_lines.append("- Keep supporting material out of this Skill unless it is essential.")

    examples = "\n".join(f"- {example}" for example in plan.examples if example.strip())
    if not examples:
        examples = "- Add one or two concrete user requests before publishing."

    constraints = ""
    if plan.constraints:
        constraint_lines = "\n".join(f"- {constraint}" for constraint in plan.constraints)
        constraints = f"""
## Source-Grounded Rules

{constraint_lines}"""

    return f"""---
name: {skill_name}
description: {description}
---

# {display_name(skill_name)}

## Objective

{brief}

## Workflow

1. Restate the task outcome and identify the relevant inputs.
2. Choose the smallest resource set needed for the task.
3. Follow the project or domain-specific procedure before general reasoning.
4. Validate the output against concrete acceptance criteria.
5. Surface uncertainty, missing inputs, or unsafe actions before proceeding.

## Resources

{chr(10).join(resource_lines)}
{constraints}

## Examples

{examples}

## Quality Bar

- Keep output grounded in the provided materials.
- Avoid broad claims that are not supported by the task context.
- Prefer deterministic scripts for fragile or repetitive transformations.
- Ask for approval before actions with external side effects.
"""


def _render_openai_yaml(plan: SkillPlan) -> str:
    skill_name = normalize_skill_name(plan.name)
    label = display_name(skill_name)
    short_description = plan.description.strip().replace('"', "'")
    default_prompt = f"Use ${skill_name} to complete the task with its documented workflow."
    return f"""display_name: "{label}"
short_description: "{short_description}"
default_prompt: "{default_prompt}"
"""


def _render_reference(plan: SkillPlan) -> str:
    return f"""# Domain Reference

Add detailed domain rules, schemas, examples, or API notes here.

Source brief:

{plan.brief.strip()}
"""


def _render_source_index(plan: SkillPlan) -> str:
    source_lines = "\n".join(
        f"- `{source.path}` ({source.kind}, {source.size_bytes} bytes, sha256 `{source.sha256}`)"
        for source in plan.sources
    )
    terminology = _render_optional_list("Extracted Terminology", plan.terminology)
    tools = _render_optional_list("Observed Tool Candidates", plan.tool_candidates)
    failures = _render_optional_list("Observed Failure Cases", plan.failure_cases)
    review_notes = _render_optional_list("Review Notes", plan.review_notes)
    return f"""# Source Index

Use the original materials as the source of truth. This file records provenance and compact
extractions; it does not copy the indexed documents.

## Sources

{source_lines}
{terminology}{tools}{failures}{review_notes}
"""


def _render_optional_list(title: str, items: tuple[str, ...]) -> str:
    if not items:
        return ""
    lines = "\n".join(f"- {item}" for item in items)
    return f"\n## {title}\n\n{lines}\n"


def _render_helper_script() -> str:
    return '''"""Helper script placeholder for deterministic Skill operations."""


def main() -> int:
    print("Replace this placeholder with a deterministic operation for the Skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _render_asset_template(plan: SkillPlan) -> str:
    skill_name = normalize_skill_name(plan.name)
    return f"""# {display_name(skill_name)} Template

Replace this file with reusable output material for `{skill_name}`.
"""
