from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

from .frontmatter import render_frontmatter
from .models import SkillPlan
from .naming import display_name, normalize_skill_name

RESOURCE_DIRS = {"references", "scripts", "assets"}
RESOURCE_PATH_PATTERN = re.compile(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+")


def validate_resource_path(path: str) -> None:
    parts = PurePosixPath(path).parts
    if (
        not RESOURCE_PATH_PATTERN.fullmatch(path)
        or parts[0] not in RESOURCE_DIRS
        or any(part in {".", ".."} for part in path.split("/"))
        or any(part.endswith((".", " ")) for part in parts)
        or any(
            part.split(".")[0].upper() in {
                "CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
                *[f"LPT{i}" for i in range(1, 10)],
            }
            for part in parts
        )
    ):
        raise ValueError(f"Resource path must be a portable relative path under references/scripts/assets: {path}")


def create_skill(plan: SkillPlan, output_dir: Path, force: bool = False) -> Path:
    skill_name = normalize_skill_name(plan.name)
    skill_dir = output_dir / skill_name
    if skill_dir.exists() and not force:
        raise FileExistsError(f"skill already exists: {skill_dir}")

    files = {
        "SKILL.md": _render_skill_md(plan),
        "agents/openai.yaml": _render_openai_yaml(plan),
    }
    seen: set[str] = set()
    for resource in plan.resource_files:
        validate_resource_path(resource.path)
        if resource.path.casefold() in seen or (plan.sources and resource.path.casefold() == "references/sources.md"):
            raise ValueError(f"Duplicate or reserved resource path: {resource.path}")
        if not resource.content.strip() or not resource.purpose.strip():
            raise ValueError(f"Resource content and purpose must be non-empty: {resource.path}")
        seen.add(resource.path.casefold())
        files[resource.path] = resource.content if resource.content.endswith("\n") else resource.content + "\n"
    if plan.sources:
        files["references/sources.md"] = _render_source_index(plan)
    normalized_paths = {path.casefold() for path in files}
    for path in files:
        if any(parent.as_posix().casefold() in normalized_paths for parent in PurePosixPath(path).parents):
            raise ValueError(f"Resource paths conflict as file and directory: {path}")

    # Preflight every destination before writing, including force-overwrite paths.
    root = output_dir.resolve()
    for relative in files:
        destination = skill_dir / relative
        if not destination.resolve().is_relative_to(root):
            raise ValueError(f"Output path escapes the selected output directory: {destination}")
        for ancestor in (destination, *destination.parents):
            if ancestor == output_dir:
                break
            if ancestor.is_symlink():
                raise ValueError(f"Refusing to write through a symbolic link: {ancestor}")
            if ancestor != destination and ancestor.exists() and not ancestor.is_dir():
                raise ValueError(f"Output parent is not a directory: {ancestor}")
        if destination.exists() and not destination.is_file():
            raise ValueError(f"Output file path is not a regular file: {destination}")

    selected_resources = set(plan.resources) & RESOURCE_DIRS
    selected_resources.update(PurePosixPath(path).parts[0] for path in files if path.split("/")[0] in RESOURCE_DIRS)
    skill_dir.mkdir(parents=True, exist_ok=True)
    for resource in selected_resources:
        (skill_dir / resource).mkdir(exist_ok=True)
    for relative, content in files.items():
        destination = skill_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    return skill_dir


def _render_skill_md(plan: SkillPlan) -> str:
    skill_name = normalize_skill_name(plan.name)
    description = plan.description.strip() or f"Use this skill when the agent needs to perform {skill_name} work."
    if len(description) > 1024:
        raise ValueError("Description must be at most 1024 characters.")
    brief = plan.brief.strip()

    resource_lines: list[str] = []
    if plan.sources:
        resource_lines.append(
            "- Load `references/sources.md` when source provenance, terminology, observed tools, "
            "or failure cases are needed."
        )
    resource_lines.extend(f"- `{resource.path}`: {resource.purpose}" for resource in plan.resource_files)
    steps = "\n".join(f"{index}. {step}" for index, step in enumerate(plan.workflow, start=1))
    if not steps:
        steps = "DRAFT: Add task-specific workflow steps before publishing."
    body = f"# {display_name(skill_name)}\n\n## Objective\n\n{brief}\n\n## Workflow\n\n{steps}\n"
    if resource_lines:
        body += "\n## Resources\n\n" + "\n".join(resource_lines) + "\n"
    body += _render_optional_list("Constraints", plan.constraints)
    body += _render_optional_list("Examples", plan.examples)
    body += _render_optional_list("Quality Checks", plan.quality_checks)
    return render_frontmatter({"name": skill_name, "description": description}, body)


def _render_openai_yaml(plan: SkillPlan) -> str:
    skill_name = normalize_skill_name(plan.name)
    label = display_name(skill_name)
    short_description = " ".join(plan.description.split())[:64]
    if len(short_description) < 25:
        short_description = f"Reusable agent workflow for {label}"[:64]
    default_prompt = f"Use ${skill_name} to complete the task with its documented workflow."
    interface = {"display_name": label, "short_description": short_description, "default_prompt": default_prompt}
    return "interface:\n" + "".join(
        f"  {key}: {json.dumps(value, ensure_ascii=False)}\n" for key, value in interface.items()
    )


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
