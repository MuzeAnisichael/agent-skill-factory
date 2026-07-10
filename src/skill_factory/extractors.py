from __future__ import annotations

import re
from typing import Sequence


MAX_BRIEF_CHARS = 800
MAX_ITEM_CHARS = 300


def extract_examples(text: str) -> list[str]:
    examples: list[str] = []
    section = ""
    prefix_pattern = re.compile(
        r"^(?:example|task|use[ -]?case|prompt|request|示例|任务|用例|请求)\s*[:：]\s*(.+)$",
        flags=re.IGNORECASE,
    )
    for raw_line in text.splitlines():
        heading = _heading(raw_line)
        if heading is not None:
            section = _section_kind(heading)
            continue
        clean = _clean_item(raw_line)
        if not clean:
            continue
        prefix_match = prefix_pattern.match(clean)
        if prefix_match:
            examples.append(truncate(prefix_match.group(1).strip(), MAX_ITEM_CHARS))
        elif section == "examples" and _is_list_item(raw_line):
            examples.append(truncate(clean, MAX_ITEM_CHARS))
    return examples


def extract_constraints(text: str) -> list[str]:
    constraints: list[str] = []
    section = ""
    english_pattern = re.compile(
        r"\b(must|must not|should|should not|required|never|do not|don't|only|constraint)\b",
        flags=re.IGNORECASE,
    )
    chinese_markers = ("必须", "不得", "禁止", "应当", "只能", "约束", "不要")
    for raw_line in text.splitlines():
        heading = _heading(raw_line)
        if heading is not None:
            section = _section_kind(heading)
            continue
        clean = _clean_item(raw_line)
        if not clean:
            continue
        if english_pattern.search(clean) or any(marker in clean for marker in chinese_markers):
            constraints.append(truncate(clean, MAX_ITEM_CHARS))
        elif section == "constraints" and _is_list_item(raw_line):
            constraints.append(truncate(clean, MAX_ITEM_CHARS))
    return constraints


def extract_terminology(text: str) -> list[str]:
    terms: list[str] = []
    for match in re.finditer(r"`([^`\r\n]{2,80})`", text):
        value = match.group(1).strip()
        if value and not value.startswith(("http://", "https://")):
            terms.append(value)

    section = ""
    for raw_line in text.splitlines():
        heading = _heading(raw_line)
        if heading is not None:
            section = _section_kind(heading)
            continue
        if section == "terminology" and _is_list_item(raw_line):
            clean = _clean_item(raw_line)
            if clean and "`" not in clean:
                terms.append(truncate(clean, MAX_ITEM_CHARS))
    return terms


def extract_summary(text: str) -> str:
    parts: list[str] = []
    in_fence = False
    in_frontmatter = False
    for index, raw_line in enumerate(text.splitlines()):
        stripped = raw_line.strip()
        if index == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        heading = _heading(raw_line)
        if heading is not None:
            if parts and _section_kind(heading):
                break
            continue
        if in_fence or not stripped or _is_list_item(raw_line):
            continue
        clean = _clean_item(raw_line)
        if not clean or clean in {"---", "***"}:
            continue
        parts.append(clean)
        if len(" ".join(parts)) >= MAX_BRIEF_CHARS:
            break
    return truncate(" ".join(parts), MAX_BRIEF_CHARS)


def join_brief(parts: Sequence[str]) -> str:
    clean_parts = dedupe(parts, 6)
    return truncate(" ".join(clean_parts), MAX_BRIEF_CHARS)


def dedupe(items: Sequence[str], limit: int) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean = item.strip()
        key = clean.casefold()
        if not clean or key in seen:
            continue
        seen.add(key)
        result.append(clean)
        if len(result) >= limit:
            break
    return tuple(result)


def truncate(value: str, limit: int) -> str:
    clean = " ".join(value.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def _heading(line: str) -> str | None:
    match = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
    return match.group(1).strip() if match else None


def _section_kind(heading: str) -> str:
    lower = heading.casefold()
    if any(
        marker in lower
        for marker in ("example", "task", "use case", "prompt", "示例", "任务", "用例")
    ):
        return "examples"
    if any(
        marker in lower
        for marker in ("constraint", "requirement", "rule", "policy", "约束", "要求", "规则")
    ):
        return "constraints"
    if any(
        marker in lower
        for marker in ("glossary", "terminology", "vocabulary", "术语", "词汇")
    ):
        return "terminology"
    return ""


def _is_list_item(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*+] |\d+[.)]\s+)", line))


def _clean_item(line: str) -> str:
    return re.sub(r"^\s*(?:[-*+] |\d+[.)]\s+)", "", line).strip()
