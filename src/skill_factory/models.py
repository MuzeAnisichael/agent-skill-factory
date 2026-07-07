from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class SkillPlan:
    name: str
    description: str
    brief: str
    resources: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class LintFinding:
    severity: Severity
    code: str
    message: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class LintReport:
    target: Path
    findings: list[LintFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == Severity.WARNING)

    @property
    def passed(self) -> bool:
        return self.error_count == 0

    def add(self, severity: Severity, code: str, message: str, path: Path | str) -> None:
        self.findings.append(
            LintFinding(
                severity=severity,
                code=code,
                message=message,
                path=str(path),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": str(self.target),
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "findings": [finding.to_dict() for finding in self.findings],
        }
