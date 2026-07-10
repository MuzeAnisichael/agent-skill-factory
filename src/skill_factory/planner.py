from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from .generator import RESOURCE_DIRS
from .llm import BaseLLMClient, LLMError
from .models import SkillPlan, SourceReference
from .naming import normalize_skill_name

SYSTEM_PROMPT = """You create concise, safe Agent Skill plans.
Return only a single JSON object. Do not include Markdown fences.
The JSON object must contain:
- name: short lowercase skill name or title
- description: one sentence that explains capability and when to use the skill
- brief: concise objective and workflow summary
- resources: array containing zero or more of references, scripts, assets
- examples: array of concrete user prompts that should trigger the skill
"""


def plan_skill_with_llm(
    client: BaseLLMClient,
    brief: str,
    name: str | None = None,
    description: str | None = None,
    resources: tuple[str, ...] = (),
    examples: tuple[str, ...] = (),
) -> SkillPlan:
    if not brief.strip():
        raise ValueError("LLM planning requires a non-empty brief.")

    prompt = build_planner_prompt(
        brief=brief,
        name=name,
        description=description,
        resources=resources,
        examples=examples,
    )
    response = client.generate(prompt, system=SYSTEM_PROMPT)
    payload = parse_plan_payload(response.text)
    return skill_plan_from_payload(
        payload,
        fallback_brief=brief,
        override_name=name,
        override_description=description,
        override_resources=resources,
        extra_examples=examples,
    )


def build_planner_prompt(
    brief: str,
    name: str | None = None,
    description: str | None = None,
    resources: tuple[str, ...] = (),
    examples: tuple[str, ...] = (),
) -> str:
    parts = [
        "Create an Agent Skill plan from this source material.",
        "",
        "Source material:",
        brief.strip(),
    ]
    if name:
        parts.extend(["", f"Preferred name: {name}"])
    if description:
        parts.extend(["", f"Preferred description: {description}"])
    if resources:
        parts.extend(["", f"Preferred resources: {', '.join(resources)}"])
    if examples:
        parts.extend(["", "Known trigger examples:", *[f"- {example}" for example in examples]])
    parts.extend(
        [
            "",
            "Rules:",
            "- Keep the plan specific to the source material.",
            "- Choose scripts only when deterministic repeated operations are useful.",
            "- Choose references only when detailed domain material should be loaded later.",
            "- Choose assets only when reusable templates or static files are useful.",
            "- Avoid unsafe side effects unless the brief explicitly requires them.",
        ]
    )
    return "\n".join(parts)


def parse_plan_payload(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMError("LLM planner response did not contain a JSON object.")
    candidate = text[start : end + 1]
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM planner returned invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise LLMError("LLM planner JSON must be an object.")
    return payload


def skill_plan_from_payload(
    payload: dict[str, Any],
    fallback_brief: str,
    override_name: str | None = None,
    override_description: str | None = None,
    override_resources: tuple[str, ...] = (),
    extra_examples: tuple[str, ...] = (),
) -> SkillPlan:
    raw_name = override_name or _string(payload.get("name")) or "generated-skill"
    name = normalize_skill_name(raw_name)
    description = (
        override_description
        or _string(payload.get("description"))
        or f"Use this skill when the agent needs to complete {name} tasks with a reusable workflow."
    )
    brief = _string(payload.get("brief")) or fallback_brief
    resources = override_resources or _resources(payload.get("resources"))
    examples = _strings(payload.get("examples")) + tuple(example for example in extra_examples if example.strip())
    return SkillPlan(
        name=name,
        description=description,
        brief=brief,
        resources=resources,
        examples=examples,
        constraints=_strings(payload.get("constraints")),
        terminology=_strings(payload.get("terminology")),
        tool_candidates=_strings(payload.get("tool_candidates")),
        failure_cases=_strings(payload.get("failure_cases")),
        sources=_sources(payload.get("sources")),
        review_notes=_strings(payload.get("review_notes")),
    )


def skill_plan_to_dict(plan: SkillPlan) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "name": plan.name,
        "description": plan.description,
        "brief": plan.brief,
        "resources": list(plan.resources),
        "examples": list(plan.examples),
        "constraints": list(plan.constraints),
        "terminology": list(plan.terminology),
        "tool_candidates": list(plan.tool_candidates),
        "failure_cases": list(plan.failure_cases),
        "sources": [
            {
                "path": source.path,
                "sha256": source.sha256,
                "kind": source.kind,
                "size_bytes": source.size_bytes,
            }
            for source in plan.sources
        ],
        "review_notes": list(plan.review_notes),
    }


def load_skill_plan(path: Path) -> SkillPlan:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read SkillPlan: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"SkillPlan is not valid JSON: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise ValueError("SkillPlan JSON must be an object.")
    schema_version = payload.get("schema_version", 1)
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        raise ValueError(f"Unsupported SkillPlan schema_version: {schema_version}")
    for field_name in ("name", "description", "brief"):
        if not isinstance(payload.get(field_name), str) or not payload[field_name].strip():
            raise ValueError(f"SkillPlan field '{field_name}' must be a non-empty string.")
    _validate_string_array(payload, "resources")
    for field_name in (
        "examples",
        "constraints",
        "terminology",
        "tool_candidates",
        "failure_cases",
        "review_notes",
    ):
        _validate_string_array(payload, field_name)
    invalid_resources = sorted(set(payload.get("resources", [])) - RESOURCE_DIRS)
    if invalid_resources:
        raise ValueError(f"Unknown SkillPlan resources: {', '.join(invalid_resources)}")
    _validate_sources(payload)

    return skill_plan_from_payload(payload, fallback_brief=payload["brief"])


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _resources(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        raw_values = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        raw_values = [item.strip() for item in value if isinstance(item, str)]
    else:
        raw_values = []
    return tuple(resource for resource in raw_values if resource in RESOURCE_DIRS)


def _sources(value: Any) -> tuple[SourceReference, ...]:
    if not isinstance(value, list):
        return ()
    sources: list[SourceReference] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        path = _string(item.get("path"))
        sha256 = _string(item.get("sha256"))
        kind = _string(item.get("kind")) or "document"
        size_bytes = item.get("size_bytes", 0)
        if not path or not sha256 or kind not in {"document", "trace"}:
            continue
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
            continue
        sources.append(
            SourceReference(path=path, sha256=sha256, kind=kind, size_bytes=size_bytes)
        )
    return tuple(sources)


def _validate_string_array(payload: dict[str, Any], field_name: str) -> None:
    if field_name not in payload:
        return
    value = payload[field_name]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"SkillPlan field '{field_name}' must be an array of strings.")


def _validate_sources(payload: dict[str, Any]) -> None:
    if "sources" not in payload:
        return
    sources = payload["sources"]
    if not isinstance(sources, list):
        raise ValueError("SkillPlan field 'sources' must be an array.")
    allowed_fields = {"path", "sha256", "kind", "size_bytes"}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"SkillPlan sources[{index}] must be an object.")
        unknown_fields = sorted(set(source) - allowed_fields)
        if unknown_fields:
            raise ValueError(
                f"Unknown fields in SkillPlan sources[{index}]: {', '.join(unknown_fields)}"
            )
        path = source.get("path")
        sha256 = source.get("sha256")
        kind = source.get("kind", "document")
        size_bytes = source.get("size_bytes", 0)
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"SkillPlan sources[{index}].path must be non-empty.")
        normalized_path = path.replace("\\", "/")
        if (
            Path(path).is_absolute()
            or PurePosixPath(normalized_path).is_absolute()
            or ".." in PurePosixPath(normalized_path).parts
            or any(character in path for character in ("\r", "\n", "`"))
        ):
            raise ValueError(
                f"SkillPlan sources[{index}].path must be a safe relative display path."
            )
        if (
            not isinstance(sha256, str)
            or len(sha256) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in sha256)
        ):
            raise ValueError(f"SkillPlan sources[{index}].sha256 must be a SHA-256 hex digest.")
        if kind not in {"document", "trace"}:
            raise ValueError(f"SkillPlan sources[{index}].kind must be document or trace.")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
            raise ValueError(f"SkillPlan sources[{index}].size_bytes must be a non-negative integer.")
