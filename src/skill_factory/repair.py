from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .evaluator import DEFAULT_EVAL_PATH, EvalError, evaluate_skill
from .frontmatter import parse_frontmatter
from .linter import lint_skill
from .models import LintReport, Severity
from .naming import display_name
from .runner import EvalRunner
from .security import dangerous_messages


@dataclass(frozen=True)
class RepairAction:
    id: str
    kind: str
    path: str
    description: str
    reason: str
    payload: dict[str, Any] = field(default_factory=dict)
    risky: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepairPlan:
    skill_path: Path
    actions: list[RepairAction] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    lint: dict[str, Any] = field(default_factory=dict)
    eval: dict[str, Any] = field(default_factory=dict)

    @property
    def actionable_count(self) -> int:
        return sum(1 for action in self.actions if not action.risky)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_path": str(self.skill_path),
            "actionable_count": self.actionable_count,
            "actions": [action.to_dict() for action in self.actions],
            "blocked": self.blocked,
            "lint": self.lint,
            "eval": self.eval,
        }


@dataclass(frozen=True)
class RepairResult:
    skill_path: Path
    accepted: bool
    applied: list[RepairAction]
    skipped: list[RepairAction]
    rolled_back: bool
    reason: str
    before: dict[str, Any]
    after: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_path": str(self.skill_path),
            "accepted": self.accepted,
            "rolled_back": self.rolled_back,
            "reason": self.reason,
            "applied": [action.to_dict() for action in self.applied],
            "skipped": [action.to_dict() for action in self.skipped],
            "before": self.before,
            "after": self.after,
        }


class RepairError(RuntimeError):
    """Raised when a repair plan cannot be created or applied."""


def plan_repairs(
    skill_path: Path,
    eval_path: Path | None = None,
    max_lines: int = 500,
    include_eval: bool = True,
    runner: EvalRunner | None = None,
) -> RepairPlan:
    skill_dir = _resolve_skill_dir(skill_path)
    skill_file = skill_dir / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")
    lint_report = lint_skill(skill_dir, max_lines=max_lines)
    plan = RepairPlan(skill_path=skill_dir)
    plan.lint = _lint_summary(lint_report)

    _add_lint_actions(plan, skill_dir, text, lint_report, max_lines=max_lines)

    if include_eval:
        selected_eval_path = eval_path or (skill_dir / DEFAULT_EVAL_PATH)
        if selected_eval_path.exists():
            try:
                eval_report = evaluate_skill(
                    skill_dir,
                    eval_path=selected_eval_path,
                    include_lint=False,
                    runner=runner,
                )
                plan.eval = eval_report.to_dict()
                _add_eval_actions(plan, skill_dir, text, selected_eval_path)
            except EvalError as exc:
                plan.eval = {"status": "error", "message": str(exc)}
                plan.blocked.append(f"Eval configuration must be fixed manually: {exc}")
        else:
            plan.eval = {"status": "missing", "path": str(selected_eval_path)}

    _deduplicate_actions(plan)
    return plan


def apply_repairs(
    skill_path: Path,
    eval_path: Path | None = None,
    max_lines: int = 500,
    include_eval: bool = True,
    runner: EvalRunner | None = None,
    allow_risky: bool = False,
    dry_run: bool = False,
) -> RepairResult:
    skill_dir = _resolve_skill_dir(skill_path)
    plan = plan_repairs(skill_dir, eval_path=eval_path, max_lines=max_lines, include_eval=include_eval, runner=runner)
    before = _quality_snapshot(skill_dir, eval_path=eval_path, include_eval=include_eval, runner=runner, max_lines=max_lines)
    applicable = [
        action
        for action in plan.actions
        if action.kind != "manual_review" and (allow_risky or not action.risky)
    ]
    skipped = [action for action in plan.actions if action not in applicable]

    if dry_run:
        return RepairResult(skill_dir, True, [], plan.actions, False, "Dry run; no files changed.", before, before)
    if not applicable:
        return RepairResult(skill_dir, False, [], skipped, False, "No applicable repair actions.", before, before)

    skill_file = skill_dir / "SKILL.md"
    original_skill_text = skill_file.read_text(encoding="utf-8")
    created_files: list[Path] = []
    applied: list[RepairAction] = []

    try:
        updated_text = original_skill_text
        for action in applicable:
            updated_text, created = _apply_action(skill_dir, updated_text, action)
            created_files.extend(created)
            applied.append(action)
        skill_file.write_text(updated_text, encoding="utf-8")

        after = _quality_snapshot(skill_dir, eval_path=eval_path, include_eval=include_eval, runner=runner, max_lines=max_lines)
        accepted, reason = _accept_repair(before, after, applied)
        if not accepted:
            _rollback(skill_file, original_skill_text, created_files)
            rolled_back = True
            final_after = _quality_snapshot(
                skill_dir,
                eval_path=eval_path,
                include_eval=include_eval,
                runner=runner,
                max_lines=max_lines,
            )
        else:
            rolled_back = False
            final_after = after
        return RepairResult(skill_dir, accepted, applied, skipped, rolled_back, reason, before, final_after)
    except Exception as exc:
        _rollback(skill_file, original_skill_text, created_files)
        raise RepairError(f"Repair failed and changes were rolled back: {exc}") from exc


def format_repair_plan(plan: RepairPlan) -> str:
    lines = [
        f"Repair plan for {plan.skill_path}",
        f"Actionable actions: {plan.actionable_count}",
    ]
    for action in plan.actions:
        marker = "MANUAL" if action.risky else "APPLY"
        lines.append(f"{marker} {action.id}: {action.description} ({action.path})")
    for item in plan.blocked:
        lines.append(f"BLOCKED: {item}")
    return "\n".join(lines)


def format_repair_result(result: RepairResult) -> str:
    status = "ACCEPTED" if result.accepted else "REJECTED"
    lines = [
        f"{status} repair for {result.skill_path}",
        f"Applied actions: {len(result.applied)}",
        f"Skipped actions: {len(result.skipped)}",
        f"Rolled back: {result.rolled_back}",
        f"Reason: {result.reason}",
    ]
    return "\n".join(lines)


def repair_plan_to_json(plan: RepairPlan) -> str:
    return json.dumps(plan.to_dict(), indent=2, sort_keys=True)


def repair_result_to_json(result: RepairResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)


def _add_lint_actions(plan: RepairPlan, skill_dir: Path, text: str, report: LintReport, max_lines: int) -> None:
    parsed = parse_frontmatter(text)
    name = parsed.data.get("name") or skill_dir.name
    description = parsed.data.get("description", "")
    for finding in report.findings:
        if finding.code == "frontmatter.description.missing":
            plan.actions.append(
                RepairAction(
                    id="description.set",
                    kind="set_description",
                    path=str(skill_dir / "SKILL.md"),
                    description="Add a trigger-oriented frontmatter description.",
                    reason=finding.message,
                    payload={"description": _default_description(name)},
                )
            )
        elif finding.code in {"frontmatter.description.short", "frontmatter.description.trigger_weak"}:
            plan.actions.append(
                RepairAction(
                    id="description.expand",
                    kind="set_description",
                    path=str(skill_dir / "SKILL.md"),
                    description="Expand frontmatter description with clearer trigger context.",
                    reason=finding.message,
                    payload={"description": _expanded_description(name, description)},
                )
            )
        elif finding.code == "resource.missing":
            resource_path = _relative_to_skill(skill_dir, Path(finding.path))
            plan.actions.append(
                RepairAction(
                    id=f"resource.create:{resource_path}",
                    kind="create_resource",
                    path=str(skill_dir / resource_path),
                    description=f"Create missing referenced resource `{resource_path}`.",
                    reason=finding.message,
                    payload={"resource_path": resource_path.as_posix()},
                )
            )
        elif finding.code == "body.too_long":
            plan.actions.append(
                RepairAction(
                    id="body.split_overflow",
                    kind="split_body",
                    path=str(skill_dir / "SKILL.md"),
                    description="Move overflow body content into `references/overflow.md`.",
                    reason=finding.message,
                    payload={
                        "reference_path": "references/overflow.md",
                        "max_lines": max_lines,
                    },
                )
            )
        elif finding.code.startswith("security."):
            plan.blocked.append(f"{finding.code}: {finding.message} ({finding.path})")
            plan.actions.append(
                RepairAction(
                    id=f"manual_review:{finding.code}",
                    kind="manual_review",
                    path=finding.path,
                    description="Security-related finding requires manual review.",
                    reason=finding.message,
                    risky=True,
                )
            )


def _add_eval_actions(plan: RepairPlan, skill_dir: Path, text: str, eval_path: Path) -> None:
    payload = _read_json(eval_path)
    parsed = parse_frontmatter(text)
    skill_text = "\n".join([parsed.data.get("description", ""), parsed.body]).lower()
    requirements: list[str] = []

    for case in payload.get("task_tests", []):
        for assertion in case.get("assertions", []):
            requirements.extend(_missing_positive_assertions(assertion, skill_text))
    for case in payload.get("runner_tests", []):
        for assertion in case.get("assertions", []):
            requirements.extend(_missing_positive_assertions(assertion, skill_text))

    safe_requirements = []
    for requirement in requirements:
        if _looks_dangerous(requirement):
            plan.blocked.append(f"Eval assertion looks unsafe and requires manual review: {requirement}")
        elif requirement not in safe_requirements:
            safe_requirements.append(requirement)

    if safe_requirements:
        plan.actions.append(
            RepairAction(
                id="eval.add_requirements",
                kind="append_requirements",
                path=str(skill_dir / "SKILL.md"),
                description="Add missing eval-required terms to the Skill body.",
                reason="Failed eval assertions require explicit Skill guidance.",
                payload={"requirements": safe_requirements},
            )
        )


def _apply_action(skill_dir: Path, text: str, action: RepairAction) -> tuple[str, list[Path]]:
    created: list[Path] = []
    if action.kind == "set_description":
        return _set_frontmatter_value(text, "description", action.payload["description"]), created
    if action.kind == "create_resource":
        resource_path = skill_dir / action.payload["resource_path"]
        if not resource_path.exists():
            resource_path.parent.mkdir(parents=True, exist_ok=True)
            resource_path.write_text(_resource_placeholder(action.payload["resource_path"]), encoding="utf-8")
            created.append(resource_path)
        return text, created
    if action.kind == "append_requirements":
        return _append_requirements(text, tuple(action.payload.get("requirements", []))), created
    if action.kind == "split_body":
        return _split_body(skill_dir, text, action.payload["reference_path"], int(action.payload["max_lines"]))
    if action.kind == "manual_review":
        return text, created
    raise RepairError(f"Unsupported repair action kind: {action.kind}")


def _set_frontmatter_value(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return f"---\n{key}: {value}\n---\n\n{text}"

    close_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            close_index = index
            break
    if close_index is None:
        return text

    replaced = False
    for index in range(1, close_index):
        if lines[index].split(":", 1)[0].strip() == key and ":" in lines[index]:
            lines[index] = f"{key}: {value}"
            replaced = True
            break
    if not replaced:
        lines.insert(close_index, f"{key}: {value}")
    return "\n".join(lines) + "\n"


def _append_requirements(text: str, requirements: tuple[str, ...]) -> str:
    if not requirements:
        return text
    lines = text.rstrip().splitlines()
    lower_text = text.lower()
    additions = [requirement for requirement in requirements if requirement.lower() not in lower_text]
    if not additions:
        return text
    lines.extend(["", "## Repair Notes", ""])
    lines.extend(f"- Ensure the Skill output or guidance covers `{requirement}`." for requirement in additions)
    return "\n".join(lines) + "\n"


def _split_body(skill_dir: Path, text: str, reference_path: str, max_lines: int) -> tuple[str, list[Path]]:
    prefix, body = _split_frontmatter(text)
    body_lines = body.splitlines()
    if len(body_lines) <= max_lines:
        return text, []

    keep_count = max(1, max_lines - 4)
    kept = body_lines[:keep_count]
    overflow = body_lines[keep_count:]
    reference = _unique_path(skill_dir / reference_path)
    actual_reference_path = reference.relative_to(skill_dir).as_posix()
    reference.parent.mkdir(parents=True, exist_ok=True)
    created = []
    if not reference.exists():
        created.append(reference)
    reference.write_text("# Overflow Reference\n\n" + "\n".join(overflow).strip() + "\n", encoding="utf-8")
    kept.extend(["", "## Additional Details", "", f"Load `{actual_reference_path}` for extended details."])
    return prefix + "\n".join(kept).rstrip() + "\n", created


def _split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            prefix = "\n".join(lines[: index + 1]) + "\n\n"
            body = "\n".join(lines[index + 1 :]).lstrip("\n")
            return prefix, body
    return "", text


def _quality_snapshot(
    skill_dir: Path,
    eval_path: Path | None,
    include_eval: bool,
    runner: EvalRunner | None,
    max_lines: int,
) -> dict[str, Any]:
    lint_report = lint_skill(skill_dir, max_lines=max_lines)
    snapshot: dict[str, Any] = {
        "lint_error_count": lint_report.error_count,
        "lint_warning_count": lint_report.warning_count,
        "lint_passed": lint_report.passed,
        "eval_passed_count": 0,
        "eval_total_count": 0,
        "eval_passed": None,
    }
    selected_eval_path = eval_path or (skill_dir / DEFAULT_EVAL_PATH)
    if include_eval and selected_eval_path.exists():
        try:
            eval_report = evaluate_skill(skill_dir, eval_path=selected_eval_path, include_lint=False, runner=runner)
            snapshot.update(
                {
                    "eval_passed_count": eval_report.passed_count,
                    "eval_total_count": eval_report.total_count,
                    "eval_passed": eval_report.passed,
                }
            )
        except EvalError as exc:
            snapshot["eval_error"] = str(exc)
    return snapshot


def _accept_repair(before: dict[str, Any], after: dict[str, Any], applied: list[RepairAction]) -> tuple[bool, str]:
    if after["lint_error_count"] > before["lint_error_count"]:
        return False, "Lint error count increased."
    if after["eval_passed_count"] < before["eval_passed_count"]:
        return False, "Eval passed count regressed."
    improved = (
        after["lint_error_count"] < before["lint_error_count"]
        or after["lint_warning_count"] < before["lint_warning_count"]
        or after["eval_passed_count"] > before["eval_passed_count"]
    )
    if improved:
        return True, "Repair improved lint or eval quality."
    if applied and after["lint_error_count"] <= before["lint_error_count"]:
        return True, "Repair preserved quality without regressions."
    return False, "Repair did not improve or preserve measurable quality."


def _rollback(skill_file: Path, original_skill_text: str, created_files: list[Path]) -> None:
    skill_file.write_text(original_skill_text, encoding="utf-8")
    for path in created_files:
        if path.exists():
            path.unlink()
        _remove_empty_parents(path.parent, stop=skill_file.parent)


def _remove_empty_parents(path: Path, stop: Path) -> None:
    current = path
    while current != stop and current.exists():
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def _resolve_skill_dir(skill_path: Path) -> Path:
    selected = skill_path.resolve()
    if selected.is_file() and selected.name == "SKILL.md":
        selected = selected.parent
    if not selected.exists():
        raise RepairError(f"Skill path does not exist: {skill_path}")
    if not (selected / "SKILL.md").is_file():
        raise RepairError(f"Missing SKILL.md under Skill path: {selected}")
    return selected


def _lint_summary(report: LintReport) -> dict[str, Any]:
    return {
        "passed": report.passed,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "findings": [finding.to_dict() for finding in report.findings],
    }


def _deduplicate_actions(plan: RepairPlan) -> None:
    seen: set[str] = set()
    actions: list[RepairAction] = []
    for action in plan.actions:
        if action.id in seen:
            continue
        actions.append(action)
        seen.add(action.id)
    plan.actions = actions


def _default_description(name: str) -> str:
    return (
        f"Use this skill when the agent needs to perform {display_name(name).lower()} "
        "work with a reusable, validated workflow."
    )


def _expanded_description(name: str, description: str) -> str:
    base = description.strip() or _default_description(name)
    if "use this skill when" not in base.lower():
        base = f"Use this skill when the agent needs to {base[0].lower() + base[1:]}"
    if len(base) < 80:
        base = f"{base.rstrip('.')} while following project-specific resources, examples, and validation checks."
    return base


def _relative_to_skill(skill_dir: Path, path: Path) -> Path:
    try:
        return path.resolve().relative_to(skill_dir.resolve())
    except ValueError:
        return Path(path.name)


def _resource_placeholder(resource_path: str) -> str:
    return f"""# {Path(resource_path).stem.replace('-', ' ').title()}

Add the missing reference material required by `SKILL.md`.
"""


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(1, 100):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RepairError(f"Could not find a unique path near {path}.")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RepairError(f"Invalid JSON at {path}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise RepairError(f"Expected JSON object at {path}.")
    return payload


def _missing_positive_assertions(assertion: Any, skill_text: str) -> list[str]:
    if isinstance(assertion, str):
        return [] if assertion.lower() in skill_text else [assertion]
    if not isinstance(assertion, dict):
        return []
    if "contains" in assertion:
        value = str(assertion["contains"]).strip()
        return [] if value.lower() in skill_text else [value]
    if "all_contains" in assertion and isinstance(assertion["all_contains"], list):
        return [str(item).strip() for item in assertion["all_contains"] if str(item).strip().lower() not in skill_text]
    if "any_contains" in assertion and isinstance(assertion["any_contains"], list):
        existing = [str(item).strip() for item in assertion["any_contains"] if str(item).strip().lower() in skill_text]
        if existing:
            return []
        for item in assertion["any_contains"]:
            value = str(item).strip()
            if value:
                return [value]
    return []


def _looks_dangerous(value: str) -> bool:
    return bool(dangerous_messages(value))
