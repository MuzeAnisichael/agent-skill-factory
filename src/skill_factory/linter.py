from __future__ import annotations

import json
import re
from pathlib import Path

from .frontmatter import parse_frontmatter
from .models import LintReport, Severity
from .naming import NAME_PATTERN

ALLOWED_FRONTMATTER_KEYS = {"name", "description"}
AUXILIARY_DOC_NAMES = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}
DANGEROUS_PATTERNS = {
    r"\brm\s+-rf\b": "destructive recursive delete command",
    r"\bremove-item\b.*\b-recurse\b": "destructive recursive delete command",
    r"\bcurl\b.*\|\s*(?:sh|bash|powershell)": "download-and-execute shell pipeline",
    r"\bsecrets?\b.*\b(send|post|upload|exfiltrate)\b": "secret exfiltration language",
    r"\bdisable\b.*\b(security|approval|sandbox|guardrail)\b": "security bypass language",
}
GENERIC_FILLER = (
    "best practices",
    "high quality",
    "leverage ai",
    "be helpful",
    "do the task",
)
RESOURCE_REF_PATTERN = re.compile(r"(?:references|scripts|assets)/[A-Za-z0-9_.\-/]+")


def lint_skill(path: Path, max_lines: int = 500) -> LintReport:
    target = path.resolve()
    report = LintReport(target=target)
    skill_dir = target if target.is_dir() else target.parent
    skill_file = target if target.name == "SKILL.md" else skill_dir / "SKILL.md"

    if not skill_dir.exists():
        report.add(Severity.ERROR, "path.missing", "Skill path does not exist.", target)
        return report

    if not skill_file.exists():
        report.add(Severity.ERROR, "skill.missing", "Missing required SKILL.md.", skill_file)
        return report

    text = skill_file.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    for error in frontmatter.errors:
        report.add(Severity.ERROR, "frontmatter.invalid", error, skill_file)

    name = frontmatter.data.get("name", "")
    description = frontmatter.data.get("description", "")
    _lint_frontmatter(report, skill_file, skill_dir, name, description, frontmatter.data)
    _lint_body(report, skill_file, frontmatter.body, max_lines)
    _lint_resource_references(report, skill_dir, frontmatter.body)
    _lint_resource_layout(report, skill_dir)
    _lint_scripts(report, skill_dir)

    return report


def report_to_json(report: LintReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True)


def format_report(report: LintReport) -> str:
    if not report.findings:
        return f"PASS {report.target}"

    lines = [f"{'PASS' if report.passed else 'FAIL'} {report.target}"]
    for finding in report.findings:
        lines.append(
            f"{finding.severity.value.upper()} {finding.code}: {finding.message} ({finding.path})"
        )
    return "\n".join(lines)


def _lint_frontmatter(
    report: LintReport,
    skill_file: Path,
    skill_dir: Path,
    name: str,
    description: str,
    data: dict[str, str],
) -> None:
    if not name:
        report.add(Severity.ERROR, "frontmatter.name.missing", "Missing frontmatter name.", skill_file)
    elif not NAME_PATTERN.match(name):
        report.add(
            Severity.ERROR,
            "frontmatter.name.invalid",
            "Name must use lowercase letters, digits, and hyphens, with max length 64.",
            skill_file,
        )
    elif skill_dir.name != name:
        report.add(
            Severity.ERROR,
            "frontmatter.name.folder_mismatch",
            f"Folder name '{skill_dir.name}' must match frontmatter name '{name}'.",
            skill_dir,
        )

    if not description:
        report.add(
            Severity.ERROR,
            "frontmatter.description.missing",
            "Missing frontmatter description.",
            skill_file,
        )
    else:
        lower_description = description.lower()
        if len(description) < 60:
            report.add(
                Severity.WARNING,
                "frontmatter.description.short",
                "Description is short; include capability and trigger context.",
                skill_file,
            )
        if not any(marker in lower_description for marker in ("use when", "when", "for", "trigger")):
            report.add(
                Severity.WARNING,
                "frontmatter.description.trigger_weak",
                "Description should explain when the Skill should be used.",
                skill_file,
            )

    extra_keys = set(data) - ALLOWED_FRONTMATTER_KEYS
    if extra_keys:
        report.add(
            Severity.WARNING,
            "frontmatter.extra_keys",
            f"Unexpected frontmatter keys: {', '.join(sorted(extra_keys))}.",
            skill_file,
        )


def _lint_body(report: LintReport, skill_file: Path, body: str, max_lines: int) -> None:
    lines = body.splitlines()
    if not body.strip():
        report.add(Severity.ERROR, "body.empty", "SKILL.md body is empty.", skill_file)
        return

    if len(lines) > max_lines:
        report.add(
            Severity.WARNING,
            "body.too_long",
            f"SKILL.md has {len(lines)} body lines; keep it under {max_lines}.",
            skill_file,
        )

    lower_body = body.lower()
    for pattern, message in DANGEROUS_PATTERNS.items():
        if re.search(pattern, lower_body, flags=re.IGNORECASE | re.DOTALL):
            report.add(Severity.ERROR, "security.dangerous_instruction", message, skill_file)

    filler_hits = [phrase for phrase in GENERIC_FILLER if phrase in lower_body]
    if len(filler_hits) >= 3:
        report.add(
            Severity.WARNING,
            "body.generic_filler",
            "Body contains several generic filler phrases; replace them with task-specific instructions.",
            skill_file,
        )

    if "when to use" in lower_body:
        report.add(
            Severity.WARNING,
            "body.trigger_in_body",
            "Put trigger criteria in frontmatter description, not a body 'when to use' section.",
            skill_file,
        )


def _lint_resource_references(report: LintReport, skill_dir: Path, body: str) -> None:
    for match in RESOURCE_REF_PATTERN.finditer(body):
        resource_path = skill_dir / match.group(0)
        if not resource_path.exists():
            report.add(
                Severity.ERROR,
                "resource.missing",
                f"Referenced resource does not exist: {match.group(0)}.",
                resource_path,
            )


def _lint_resource_layout(report: LintReport, skill_dir: Path) -> None:
    for doc_name in AUXILIARY_DOC_NAMES:
        path = skill_dir / doc_name
        if path.exists():
            report.add(
                Severity.WARNING,
                "layout.auxiliary_doc",
                f"Avoid auxiliary documentation inside a Skill package: {doc_name}.",
                path,
            )

    for resource_dir in ("references", "scripts", "assets"):
        path = skill_dir / resource_dir
        if path.exists() and not path.is_dir():
            report.add(
                Severity.ERROR,
                "layout.resource_not_directory",
                f"{resource_dir} must be a directory when present.",
                path,
            )


def _lint_scripts(report: LintReport, skill_dir: Path) -> None:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return

    for script in scripts_dir.rglob("*"):
        if not script.is_file():
            continue
        text = script.read_text(encoding="utf-8", errors="replace")
        for pattern, message in DANGEROUS_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                report.add(Severity.ERROR, "security.dangerous_script", message, script)
        if script.suffix == ".py":
            try:
                compile(text, str(script), "exec")
            except SyntaxError as exc:
                report.add(
                    Severity.ERROR,
                    "script.syntax_error",
                    f"Python syntax error: {exc.msg} at line {exc.lineno}.",
                    script,
                )
