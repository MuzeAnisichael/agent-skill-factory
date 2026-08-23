from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


WARNING_CODES = frozenset(
    {
        "body.generic_filler",
        "body.too_long",
        "body.trigger_in_body",
        "frontmatter.description.short",
        "frontmatter.description.trigger_weak",
        "frontmatter.extra_keys",
        "layout.auxiliary_doc",
    }
)


@dataclass(frozen=True)
class LintPolicy:
    name: str
    max_lines: int = 500
    description_min_length: int = 60
    warnings_as_errors: frozenset[str] = frozenset()


BUILTIN_POLICIES = {
    "standard": LintPolicy(name="standard"),
    "strict": LintPolicy(
        name="strict",
        max_lines=300,
        description_min_length=80,
        warnings_as_errors=WARNING_CODES,
    ),
    "permissive": LintPolicy(
        name="permissive",
        max_lines=800,
        description_min_length=40,
    ),
}

POLICY_FIELDS = {
    "schema_version",
    "name",
    "extends",
    "max_lines",
    "description_min_length",
    "warnings_as_errors",
}


def load_lint_policy(name: str = "standard", path: Path | None = None) -> LintPolicy:
    if path is None:
        try:
            return BUILTIN_POLICIES[name]
        except KeyError as exc:
            choices = ", ".join(sorted(BUILTIN_POLICIES))
            raise ValueError(f"Unknown lint policy: {name}. Use one of: {choices}.") from exc

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read lint policy: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Lint policy is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Lint policy root must be an object.")

    unknown_fields = sorted(set(payload) - POLICY_FIELDS)
    if unknown_fields:
        raise ValueError(f"Unknown lint policy fields: {', '.join(unknown_fields)}.")
    schema_version = payload.get("schema_version", 1)
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != 1
    ):
        raise ValueError("Lint policy schema_version must be 1.")

    base_name = payload.get("extends", "standard")
    if not isinstance(base_name, str) or base_name not in BUILTIN_POLICIES:
        choices = ", ".join(sorted(BUILTIN_POLICIES))
        raise ValueError(f"Lint policy extends must be one of: {choices}.")
    base = BUILTIN_POLICIES[base_name]

    policy_name = payload.get("name", path.stem)
    if not isinstance(policy_name, str) or not policy_name.strip():
        raise ValueError("Lint policy name must be a non-empty string.")
    max_lines = _positive_int(payload.get("max_lines", base.max_lines), "max_lines")
    description_min_length = _positive_int(
        payload.get("description_min_length", base.description_min_length),
        "description_min_length",
    )
    warnings = payload.get("warnings_as_errors", sorted(base.warnings_as_errors))
    if not isinstance(warnings, list) or any(
        not isinstance(item, str) or not item.strip() for item in warnings
    ):
        raise ValueError("Lint policy warnings_as_errors must be an array of non-empty strings.")
    unknown_codes = sorted(set(warnings) - WARNING_CODES)
    if unknown_codes:
        raise ValueError(f"Unknown warning codes in lint policy: {', '.join(unknown_codes)}.")

    return LintPolicy(
        name=policy_name.strip(),
        max_lines=max_lines,
        description_min_length=description_min_length,
        warnings_as_errors=frozenset(warnings),
    )


def override_max_lines(policy: LintPolicy, max_lines: int | None) -> LintPolicy:
    if max_lines is None:
        return policy
    return replace(policy, max_lines=_positive_int(max_lines, "max_lines"))


def _positive_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"Lint policy {field_name} must be a positive integer.")
    return value
