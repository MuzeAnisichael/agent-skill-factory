from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .frontmatter import parse_frontmatter
from .linter import lint_skill

DEFAULT_EVAL_PATH = Path("evals") / "evals.json"
TRIGGER_CASE_KEYS = {"id", "query", "should_trigger", "keywords", "negative_keywords"}
TASK_CASE_KEYS = {"id", "prompt", "assertions"}
ASSERTION_KEYS = {"target", "contains", "not_contains", "any_contains", "all_contains"}
ASSERTION_OPERATORS = {"contains", "not_contains", "any_contains", "all_contains"}
ASSERTION_TARGETS = {"text", "description", "body"}


@dataclass(frozen=True)
class EvalCaseResult:
    id: str
    type: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvalReport:
    skill_path: Path
    eval_path: Path
    results: list[EvalCaseResult] = field(default_factory=list)
    lint_passed: bool = True
    lint_error_count: int = 0
    lint_warning_count: int = 0

    @property
    def passed(self) -> bool:
        return self.lint_passed and all(result.passed for result in self.results)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for result in self.results if result.passed)

    @property
    def failed_count(self) -> int:
        return self.total_count - self.passed_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_path": str(self.skill_path),
            "eval_path": str(self.eval_path),
            "passed": self.passed,
            "total_count": self.total_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "lint": {
                "passed": self.lint_passed,
                "error_count": self.lint_error_count,
                "warning_count": self.lint_warning_count,
            },
            "results": [result.to_dict() for result in self.results],
        }


class EvalError(RuntimeError):
    """Raised when eval configuration cannot be loaded or interpreted."""


def evaluate_skill(skill_path: Path, eval_path: Path | None = None, include_lint: bool = True) -> EvalReport:
    skill_dir = skill_path.resolve()
    if skill_dir.is_file() and skill_dir.name == "SKILL.md":
        skill_dir = skill_dir.parent
    if not skill_dir.exists():
        raise EvalError(f"Skill path does not exist: {skill_path}")

    selected_eval_path = (eval_path or (skill_dir / DEFAULT_EVAL_PATH)).resolve()
    payload = _load_eval_payload(selected_eval_path)
    skill_text = _read_skill_text(skill_dir)
    skill_snapshot = _skill_snapshot(skill_dir, skill_text)

    report = EvalReport(skill_path=skill_dir, eval_path=selected_eval_path)
    if include_lint:
        lint_report = lint_skill(skill_dir)
        report.lint_passed = lint_report.passed
        report.lint_error_count = lint_report.error_count
        report.lint_warning_count = lint_report.warning_count

    for case in payload.get("trigger_tests", []):
        report.results.append(_evaluate_trigger_case(case, skill_snapshot))
    for case in payload.get("task_tests", []):
        report.results.append(_evaluate_task_case(case, skill_snapshot))

    return report


def format_eval_report(report: EvalReport) -> str:
    status = "PASS" if report.passed else "FAIL"
    lines = [
        f"{status} {report.skill_path}",
        f"Eval file: {report.eval_path}",
        f"Cases: {report.passed_count}/{report.total_count} passed",
        (
            "Lint: "
            f"{'passed' if report.lint_passed else 'failed'} "
            f"({report.lint_error_count} errors, {report.lint_warning_count} warnings)"
        ),
    ]
    for result in report.results:
        marker = "PASS" if result.passed else "FAIL"
        lines.append(f"{marker} {result.type}:{result.id} - {result.message}")
    return "\n".join(lines)


def eval_report_to_json(report: EvalReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True)


def _load_eval_payload(eval_path: Path) -> dict[str, Any]:
    if not eval_path.exists():
        raise EvalError(f"Eval file does not exist: {eval_path}")
    try:
        payload = json.loads(eval_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvalError(f"Invalid eval JSON at {eval_path}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise EvalError("Eval file must contain a JSON object.")
    _validate_eval_payload(payload)
    return payload


def _validate_eval_payload(payload: dict[str, Any]) -> None:
    unknown_keys = set(payload) - {"trigger_tests", "task_tests"}
    if unknown_keys:
        raise EvalError(f"Unknown eval top-level keys: {', '.join(sorted(unknown_keys))}.")

    trigger_tests = payload.get("trigger_tests", [])
    task_tests = payload.get("task_tests", [])
    if not isinstance(trigger_tests, list):
        raise EvalError("trigger_tests must be an array when present.")
    if not isinstance(task_tests, list):
        raise EvalError("task_tests must be an array when present.")
    if not trigger_tests and not task_tests:
        raise EvalError("Eval file must include at least one trigger_tests or task_tests case.")

    for index, case in enumerate(trigger_tests):
        _validate_trigger_case(case, index)
    for index, case in enumerate(task_tests):
        _validate_task_case(case, index)


def _validate_trigger_case(case: Any, index: int) -> None:
    prefix = f"trigger_tests[{index}]"
    if not isinstance(case, dict):
        raise EvalError(f"{prefix} must be an object.")
    _reject_unknown_case_keys(prefix, case, TRIGGER_CASE_KEYS)
    _require_string(case, "id", prefix)
    _require_string(case, "query", prefix)
    if "should_trigger" not in case or not isinstance(case["should_trigger"], bool):
        raise EvalError(f"{prefix}.should_trigger must be a boolean.")
    _optional_string_list(case, "keywords", prefix)
    _optional_string_list(case, "negative_keywords", prefix)


def _validate_task_case(case: Any, index: int) -> None:
    prefix = f"task_tests[{index}]"
    if not isinstance(case, dict):
        raise EvalError(f"{prefix} must be an object.")
    _reject_unknown_case_keys(prefix, case, TASK_CASE_KEYS)
    _require_string(case, "id", prefix)
    if "prompt" in case and not isinstance(case["prompt"], str):
        raise EvalError(f"{prefix}.prompt must be a string when present.")
    assertions = case.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        raise EvalError(f"{prefix}.assertions must be a non-empty array.")
    for assertion_index, assertion in enumerate(assertions):
        _validate_assertion(assertion, f"{prefix}.assertions[{assertion_index}]")


def _validate_assertion(assertion: Any, prefix: str) -> None:
    if isinstance(assertion, str):
        if not assertion.strip():
            raise EvalError(f"{prefix} must not be an empty string.")
        return
    if not isinstance(assertion, dict):
        raise EvalError(f"{prefix} must be a string or object.")
    _reject_unknown_case_keys(prefix, assertion, ASSERTION_KEYS)
    target = assertion.get("target", "text")
    if not isinstance(target, str) or target not in ASSERTION_TARGETS:
        raise EvalError(f"{prefix}.target must be one of: {', '.join(sorted(ASSERTION_TARGETS))}.")
    operators = set(assertion) & ASSERTION_OPERATORS
    if len(operators) != 1:
        raise EvalError(f"{prefix} must include exactly one assertion operator.")
    operator = next(iter(operators))
    value = assertion[operator]
    if operator in {"contains", "not_contains"}:
        if not isinstance(value, str) or not value.strip():
            raise EvalError(f"{prefix}.{operator} must be a non-empty string.")
    else:
        if not isinstance(value, list) or not value:
            raise EvalError(f"{prefix}.{operator} must be a non-empty string array.")
        _optional_string_list(assertion, operator, prefix)


def _reject_unknown_case_keys(prefix: str, value: dict[str, Any], allowed_keys: set[str]) -> None:
    unknown_keys = set(value) - allowed_keys
    if unknown_keys:
        raise EvalError(f"{prefix} has unknown keys: {', '.join(sorted(unknown_keys))}.")


def _require_string(value: dict[str, Any], key: str, prefix: str) -> None:
    if key not in value or not isinstance(value[key], str) or not value[key].strip():
        raise EvalError(f"{prefix}.{key} must be a non-empty string.")


def _optional_string_list(value: dict[str, Any], key: str, prefix: str) -> None:
    if key not in value:
        return
    if not isinstance(value[key], list) or not all(
        isinstance(item, str) and item.strip() for item in value[key]
    ):
        raise EvalError(f"{prefix}.{key} must be an array of non-empty strings.")


def _read_skill_text(skill_dir: Path) -> str:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        raise EvalError(f"Missing SKILL.md at {skill_file}")
    return skill_file.read_text(encoding="utf-8")


def _skill_snapshot(skill_dir: Path, skill_text: str) -> dict[str, str]:
    parsed = parse_frontmatter(skill_text)
    visible_text = "\n".join(
        [
            parsed.data.get("name", ""),
            parsed.data.get("description", ""),
            parsed.body,
        ]
    ).lower()
    return {
        "name": parsed.data.get("name", ""),
        "description": parsed.data.get("description", ""),
        "body": parsed.body,
        "text": visible_text,
        "path": str(skill_dir),
    }


def _evaluate_trigger_case(case: Any, skill: dict[str, str]) -> EvalCaseResult:
    case_id = _case_id(case)
    query = _string(case.get("query")).lower()
    should_trigger = bool(case.get("should_trigger"))
    keywords = _strings(case.get("keywords"))
    negative_keywords = _strings(case.get("negative_keywords"))
    skill_text = skill["text"]

    if not query:
        return EvalCaseResult(case_id, "trigger", False, "Missing query.")

    positive_signal = _contains_any(query, keywords)
    if not keywords:
        positive_signal = _word_overlap_score(query, skill_text) >= 0.18

    negative_signal = _contains_any(query, negative_keywords) or _contains_any(skill_text, negative_keywords)
    predicted = positive_signal and not negative_signal
    passed = predicted == should_trigger
    message = f"expected should_trigger={should_trigger}, predicted={predicted}"
    return EvalCaseResult(case_id, "trigger", passed, message)


def _evaluate_task_case(case: Any, skill: dict[str, str]) -> EvalCaseResult:
    case_id = _case_id(case)
    assertions = case.get("assertions", [])

    failures: list[str] = []
    for index, assertion in enumerate(assertions, start=1):
        if not _evaluate_assertion(assertion, skill):
            failures.append(f"assertion {index} failed")

    if failures:
        return EvalCaseResult(case_id, "task", False, "; ".join(failures))
    return EvalCaseResult(case_id, "task", True, f"{len(assertions)} assertions passed")


def _evaluate_assertion(assertion: Any, skill: dict[str, str]) -> bool:
    if isinstance(assertion, str):
        return assertion.lower() in skill["text"]
    if not isinstance(assertion, dict):
        return False

    target = _string(assertion.get("target")) or "text"
    text = skill.get(target, skill["text"]).lower()
    if "contains" in assertion:
        return _string(assertion.get("contains")).lower() in text
    if "not_contains" in assertion:
        return _string(assertion.get("not_contains")).lower() not in text
    if "any_contains" in assertion:
        return _contains_any(text, _strings(assertion.get("any_contains")))
    if "all_contains" in assertion:
        return all(item.lower() in text for item in _strings(assertion.get("all_contains")))
    return False


def _case_id(case: dict[str, Any]) -> str:
    return _string(case.get("id")) or "unnamed"


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item.strip().lower() for item in value if isinstance(item, str) and item.strip())


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _word_overlap_score(query: str, text: str) -> float:
    query_words = _words(query)
    if not query_words:
        return 0.0
    text_words = _words(text)
    overlap = query_words & text_words
    return len(overlap) / len(query_words)


def _words(value: str) -> set[str]:
    normalized = "".join(character.lower() if character.isalnum() else " " for character in value)
    return {word for word in normalized.split() if len(word) >= 3}
