from __future__ import annotations

import json
import re
from typing import Any

from .models import SkillPlan


MAX_TRIGGER_CASES = 12
MAX_ASSERTED_CONSTRAINTS = 6
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,}|[\u4e00-\u9fff]{2,}")
STOP_WORDS = {
    "and",
    "create",
    "from",
    "into",
    "please",
    "should",
    "that",
    "the",
    "this",
    "using",
    "with",
}


def generate_eval_payload(plan: SkillPlan) -> dict[str, Any]:
    trigger_tests: list[dict[str, Any]] = []
    seen_queries: set[str] = set()

    source_cases = [
        ("example", example) for example in plan.examples
    ] + [
        ("failure", _failure_task(failure)) for failure in plan.failure_cases
    ]
    if not source_cases:
        source_cases.append(("brief", plan.brief))

    counters: dict[str, int] = {}
    for source_kind, query in source_cases:
        normalized_query = query.strip()
        dedupe_key = normalized_query.casefold()
        if not normalized_query or dedupe_key in seen_queries:
            continue
        seen_queries.add(dedupe_key)
        counters[source_kind] = counters.get(source_kind, 0) + 1
        trigger_tests.append(
            {
                "id": f"source-{source_kind}-{counters[source_kind]:02d}",
                "query": normalized_query,
                "should_trigger": True,
                "keywords": _keywords(normalized_query, plan.terminology),
            }
        )
        if len(trigger_tests) >= MAX_TRIGGER_CASES:
            break

    assertions: list[dict[str, Any]] = []
    if plan.constraints:
        assertions.append(
            {
                "target": "body",
                "all_contains": list(plan.constraints[:MAX_ASSERTED_CONSTRAINTS]),
            }
        )
    else:
        assertions.append({"target": "body", "contains": plan.brief.strip()})

    prompt = plan.examples[0].strip() if plan.examples else plan.brief.strip()
    return {
        "trigger_tests": trigger_tests,
        "task_tests": [
            {
                "id": "source-grounding-01",
                "prompt": prompt,
                "assertions": assertions,
            }
        ],
    }


def generated_eval_json(plan: SkillPlan) -> str:
    return json.dumps(generate_eval_payload(plan), indent=2, sort_keys=True) + "\n"


def _failure_task(failure: str) -> str:
    task, separator, _detail = failure.rpartition(": ")
    return task if separator and task.strip() else failure


def _keywords(query: str, terminology: tuple[str, ...]) -> list[str]:
    lowered_query = query.casefold()
    values: list[str] = []
    for term in terminology:
        normalized = term.strip()
        if normalized and normalized.casefold() in lowered_query:
            values.append(normalized)
    for match in TOKEN_PATTERN.finditer(query):
        token = match.group(0)
        if token.casefold() not in STOP_WORDS:
            values.append(token)

    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            deduplicated.append(value)
        if len(deduplicated) == 4:
            break
    return deduplicated or [query.strip()]
