from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml


class _UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[str, Any]:
        if not isinstance(node, yaml.MappingNode):
            return super().construct_mapping(node, deep=deep)
        self.flatten_mapping(node)
        keys: set[str] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise yaml.constructor.ConstructorError(
                    None, None, "mapping keys must be strings", key_node.start_mark
                )
            if key in keys:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key: {key}", key_node.start_mark
                )
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class Frontmatter:
    data: dict[str, Any]
    body: str
    errors: tuple[str, ...] = ()

    def string(self, key: str) -> str:
        value = self.data.get(key)
        return value if isinstance(value, str) else ""


def parse_frontmatter(text: str) -> Frontmatter:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].rstrip() != "---":
        return Frontmatter({}, text, ("missing opening frontmatter delimiter",))

    close_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.rstrip() == "---"),
        None,
    )

    if close_index is None:
        return Frontmatter({}, text, ("missing closing frontmatter delimiter",))

    body = "\n".join(lines[close_index + 1 :]).lstrip("\n")
    try:
        data = yaml.load("\n".join(lines[1:close_index]) + "\n", Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f"line {mark.line + 2}, column {mark.column + 1}: " if mark else ""
        problem = getattr(exc, "problem", None) or str(exc)
        return Frontmatter({}, body, (f"{location}{problem}",))
    except RecursionError:
        return Frontmatter({}, body, ("frontmatter nesting is too deep",))
    if not isinstance(data, dict):
        return Frontmatter({}, body, ("frontmatter must be a YAML mapping",))
    return Frontmatter(data, body)


def render_frontmatter(data: dict[str, Any], body: str) -> str:
    header = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1024)
    content = body.lstrip("\n").rstrip()
    return f"---\n{header}---\n\n{content}\n"
