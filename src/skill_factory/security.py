from __future__ import annotations

import re


DANGEROUS_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\brm\s+-rf\b", "destructive recursive delete command"),
    (r"\bremove-item\b.*\b-recurse\b", "destructive recursive delete command"),
    (r"\bcurl\b.*\|\s*(?:sh|bash|powershell)", "download-and-execute shell pipeline"),
    (r"\bsecrets?\b.*\b(send|post|upload|exfiltrate)\b", "secret exfiltration language"),
    (r"\bdisable\b.*\b(security|approval|sandbox|guardrail)\b", "security bypass language"),
    (
        r"\b(?:ignore|disregard|override)\b.*\b(?:previous|prior|system|developer)\b.*\binstructions?\b",
        "prompt-injection language",
    ),
    (
        r"\b(?:reveal|print|expose|return)\b.*\b(?:system prompt|developer message|hidden instructions?)\b",
        "hidden-instruction extraction language",
    ),
)


def dangerous_messages(text: str) -> tuple[str, ...]:
    return tuple(
        message
        for pattern, message in DANGEROUS_PATTERNS
        if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    )
