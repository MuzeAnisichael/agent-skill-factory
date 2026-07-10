from __future__ import annotations

import json
from typing import Any

from .extractors import MAX_ITEM_CHARS, truncate
from .security import dangerous_messages


TRACE_ROOT_FIELDS = {"schema_version", "runs", "metadata"}
TRACE_RUN_FIELDS = {
    "id",
    "task",
    "status",
    "summary",
    "output",
    "error",
    "tools",
    "constraints",
}


class TraceError(ValueError):
    pass


def parse_trace(text: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TraceError(f"Trace file is not valid JSON ({label}): {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise TraceError(f"Trace root must be an object: {label}")
    unknown_root = sorted(set(payload) - TRACE_ROOT_FIELDS)
    if unknown_root:
        raise TraceError(f"Unknown trace fields in {label}: {', '.join(unknown_root)}")
    schema_version = payload.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        raise TraceError(f"Trace schema_version must be 1: {label}")
    if "metadata" in payload and not isinstance(payload["metadata"], dict):
        raise TraceError(f"Trace field 'metadata' must be an object: {label}")
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        raise TraceError(f"Trace field 'runs' must be a non-empty array: {label}")
    for index, run in enumerate(runs):
        _validate_run(run, label, index)
    return payload


def extract_trace_data(
    payload: dict[str, Any], label: str, review_notes: list[str]
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {
        "examples": [],
        "constraints": [],
        "tools": [],
        "failure_cases": [],
        "summaries": [],
    }
    for run in payload["runs"]:
        run_id = run["id"].strip()
        safe_values: dict[str, str] = {}
        for field_name in ("task", "summary", "output", "error"):
            value = run.get(field_name, "").strip()
            messages = dangerous_messages(value)
            if messages:
                review_notes.append(
                    f"{label} run {run_id} field {field_name}: omitted {', '.join(messages)}."
                )
                value = ""
            safe_values[field_name] = value

        result["constraints"].extend(
            _safe_items(run.get("constraints", []), label, run_id, "constraints", review_notes)
        )
        result["tools"].extend(
            _safe_items(run.get("tools", []), label, run_id, "tools", review_notes)
        )

        task = safe_values["task"]
        if run["status"] == "success" and task:
            result["examples"].append(task)
        if run["status"] == "failure" and task:
            detail = safe_values["error"] or safe_values["summary"] or safe_values["output"]
            result["failure_cases"].append(
                truncate(f"{task.rstrip(' .:;')}: {detail}" if detail else task, MAX_ITEM_CHARS)
            )
        summary = safe_values["summary"]
        if summary:
            result["summaries"].append(truncate(summary, MAX_ITEM_CHARS))
    return result


def _validate_run(run: Any, label: str, index: int) -> None:
    location = f"{label} runs[{index}]"
    if not isinstance(run, dict):
        raise TraceError(f"Trace run must be an object: {location}")
    unknown_run = sorted(set(run) - TRACE_RUN_FIELDS)
    if unknown_run:
        raise TraceError(f"Unknown trace run fields in {location}: {', '.join(unknown_run)}")
    for field_name in ("id", "task", "status"):
        if not isinstance(run.get(field_name), str) or not run[field_name].strip():
            raise TraceError(f"Trace run field '{field_name}' must be non-empty: {location}")
    if run["status"] not in {"success", "failure"}:
        raise TraceError(f"Trace run status must be success or failure: {location}")
    for field_name in ("summary", "output", "error"):
        if field_name in run and not isinstance(run[field_name], str):
            raise TraceError(f"Trace run field '{field_name}' must be a string: {location}")
    for field_name in ("tools", "constraints"):
        if field_name in run and not _is_non_empty_string_array(run[field_name]):
            raise TraceError(
                f"Trace run field '{field_name}' must be an array of strings: {location}"
            )


def _safe_items(
    items: list[str],
    label: str,
    run_id: str,
    field_name: str,
    review_notes: list[str],
) -> list[str]:
    safe: list[str] = []
    for item in items:
        messages = dangerous_messages(item)
        if messages:
            review_notes.append(
                f"{label} run {run_id} field {field_name}: omitted {', '.join(messages)}."
            )
        elif item.strip():
            safe.append(truncate(item.strip(), MAX_ITEM_CHARS))
    return safe


def _is_non_empty_string_array(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )
