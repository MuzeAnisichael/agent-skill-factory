from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Frontmatter:
    data: dict[str, str]
    body: str
    errors: tuple[str, ...] = ()


def parse_frontmatter(text: str) -> Frontmatter:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return Frontmatter({}, text, ("missing opening frontmatter delimiter",))

    close_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close_index = index
            break

    if close_index is None:
        return Frontmatter({}, text, ("missing closing frontmatter delimiter",))

    data: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(lines[1:close_index], start=2):
        stripped = line.strip()
        if not stripped:
            continue
        if ":" not in stripped:
            errors.append(f"line {line_number}: expected key: value")
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            errors.append(f"line {line_number}: empty key")
            continue
        data[key] = value

    body = "\n".join(lines[close_index + 1 :]).lstrip("\n")
    return Frontmatter(data, body, tuple(errors))
