from __future__ import annotations

import re

NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


def normalize_skill_name(raw: str) -> str:
    value = raw.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("skill name cannot be empty after normalization")
    if len(value) > 64:
        value = value[:64].rstrip("-")
    if not NAME_PATTERN.match(value):
        raise ValueError(f"invalid skill name: {value}")
    return value


def display_name(skill_name: str) -> str:
    return " ".join(part.capitalize() for part in skill_name.split("-"))
