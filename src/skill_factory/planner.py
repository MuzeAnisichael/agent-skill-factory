from __future__ import annotations

import json
from typing import Any

from .generator import RESOURCE_DIRS
from .llm import BaseLLMClient, LLMError
from .models import SkillPlan
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
    )


def skill_plan_to_dict(plan: SkillPlan) -> dict[str, Any]:
    return {
        "name": plan.name,
        "description": plan.description,
        "brief": plan.brief,
        "resources": list(plan.resources),
        "examples": list(plan.examples),
    }


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
