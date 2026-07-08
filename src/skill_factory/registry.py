from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from .evaluator import DEFAULT_EVAL_PATH, EvalError, evaluate_skill
from .frontmatter import parse_frontmatter
from .linter import lint_skill
from .models import LintReport, Severity

REGISTRY_SCHEMA_VERSION = 1
DEFAULT_REGISTRY_PATH = Path(".skill-factory") / "registry.json"
DEFAULT_EXPORT_DIRS = {
    "agent-skills": Path(".agents") / "skills",
    "codex": Path(".codex") / "skills",
    "claude-code": Path(".claude") / "skills",
}
EXPORT_TARGETS = tuple(DEFAULT_EXPORT_DIRS)
IGNORED_DIRS = {"__pycache__", ".git", ".pytest_cache"}
IGNORED_FILES = {".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


class RegistryError(RuntimeError):
    """Raised when registry, export, or install operations cannot complete."""


def register_skill(
    skill_path: Path,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    version: str = "0.1.0",
    include_eval: bool = True,
    allow_failing: bool = False,
) -> dict[str, Any]:
    skill_dir = resolve_skill_dir(skill_path)
    lint_report = lint_skill(skill_dir)
    eval_summary = _eval_summary(skill_dir, include_eval)

    if not allow_failing and not lint_report.passed:
        raise RegistryError("Refusing to register a Skill with lint errors. Use --allow-failing to override.")
    if not allow_failing and eval_summary["status"] in {"failed", "error"}:
        raise RegistryError("Refusing to register a Skill with failing evals. Use --allow-failing to override.")

    registry = load_registry(registry_path)
    metadata = _read_skill_metadata(skill_dir)
    source = hash_skill(skill_dir)
    entry = {
        "name": metadata["name"],
        "description": metadata["description"],
        "version": version,
        "path": _portable_skill_path(skill_dir, registry_path),
        "risk": _risk_summary(lint_report),
        "eval": eval_summary,
        "source": source,
        "export_targets": [],
    }
    registry["skills"][metadata["name"]] = entry
    save_registry(registry_path, registry)
    return entry


def load_registry(registry_path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    path = registry_path.resolve()
    if not path.exists():
        return {"schema_version": REGISTRY_SCHEMA_VERSION, "skills": {}}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegistryError(f"Invalid registry JSON at {path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise RegistryError("Registry file must contain a JSON object.")
    if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise RegistryError(f"Unsupported registry schema_version: {payload.get('schema_version')!r}.")
    skills = payload.get("skills")
    if not isinstance(skills, dict):
        raise RegistryError("Registry file must contain a skills object.")
    return payload


def save_registry(registry_path: Path, registry: dict[str, Any]) -> None:
    path = registry_path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def list_registry_entries(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [registry["skills"][name] for name in sorted(registry.get("skills", {}))]


def export_skill(
    skill_path: Path,
    output_dir: Path | None = None,
    target: str = "agent-skills",
    force: bool = False,
) -> Path:
    if target not in DEFAULT_EXPORT_DIRS:
        raise RegistryError(f"Unknown export target: {target}.")
    skill_dir = resolve_skill_dir(skill_path)
    destination_root = (output_dir or DEFAULT_EXPORT_DIRS[target]).resolve()
    destination = destination_root / skill_dir.name
    _copy_skill_tree(skill_dir, destination, force=force)
    return destination


def install_registered_skill(
    name: str,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    output_dir: Path | None = None,
    target: str = "agent-skills",
    force: bool = False,
) -> Path:
    registry = load_registry(registry_path)
    entry = registry.get("skills", {}).get(name)
    if not entry:
        raise RegistryError(f"Skill is not registered: {name}")
    skill_dir = _resolve_registered_path(entry, registry_path)
    return export_skill(skill_dir, output_dir=output_dir, target=target, force=force)


def format_registry_list(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "No Skills registered."

    lines = ["Registered Skills:"]
    for entry in entries:
        eval_status = entry.get("eval", {}).get("status", "unknown")
        risk_level = entry.get("risk", {}).get("level", "unknown")
        lines.append(
            f"- {entry.get('name')} {entry.get('version')} "
            f"risk={risk_level} eval={eval_status} path={entry.get('path')}"
        )
    return "\n".join(lines)


def resolve_skill_dir(skill_path: Path) -> Path:
    selected = skill_path.resolve()
    if selected.is_file() and selected.name == "SKILL.md":
        selected = selected.parent
    if not selected.exists():
        raise RegistryError(f"Skill path does not exist: {skill_path}")
    if not (selected / "SKILL.md").is_file():
        raise RegistryError(f"Missing SKILL.md under Skill path: {selected}")
    return selected


def hash_skill(skill_path: Path) -> dict[str, Any]:
    skill_dir = resolve_skill_dir(skill_path)
    files: list[dict[str, str]] = []
    package_hash = hashlib.sha256()

    for path in _iter_hashable_files(skill_dir):
        relative = path.relative_to(skill_dir).as_posix()
        file_hash = _sha256_file(path)
        files.append({"path": relative, "sha256": file_hash})
        package_hash.update(relative.encode("utf-8"))
        package_hash.update(b"\0")
        package_hash.update(file_hash.encode("ascii"))
        package_hash.update(b"\0")

    return {
        "package_sha256": package_hash.hexdigest(),
        "files": files,
    }


def _read_skill_metadata(skill_dir: Path) -> dict[str, str]:
    skill_file = skill_dir / "SKILL.md"
    parsed = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
    name = parsed.data.get("name", "")
    description = parsed.data.get("description", "")
    if not name:
        raise RegistryError("Cannot register Skill without frontmatter name.")
    return {"name": name, "description": description}


def _eval_summary(skill_dir: Path, include_eval: bool) -> dict[str, Any]:
    eval_path = skill_dir / DEFAULT_EVAL_PATH
    if not include_eval:
        return {"status": "skipped"}
    if not eval_path.exists():
        return {"status": "missing"}
    try:
        report = evaluate_skill(skill_dir)
    except EvalError as exc:
        return {"status": "error", "message": str(exc)}
    return {
        "status": "passed" if report.passed else "failed",
        "passed": report.passed_count,
        "total": report.total_count,
        "lint_passed": report.lint_passed,
    }


def _risk_summary(report: LintReport) -> dict[str, Any]:
    security_errors = [
        finding
        for finding in report.findings
        if finding.severity == Severity.ERROR and finding.code.startswith("security.")
    ]
    if security_errors:
        level = "high"
    elif report.error_count:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "lint_errors": report.error_count,
        "lint_warnings": report.warning_count,
    }


def _portable_skill_path(skill_dir: Path, registry_path: Path) -> str:
    root = _registry_root(registry_path)
    try:
        return skill_dir.relative_to(root).as_posix()
    except ValueError:
        return os.path.relpath(skill_dir, root).replace(os.sep, "/")


def _resolve_registered_path(entry: dict[str, Any], registry_path: Path) -> Path:
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise RegistryError("Registry entry is missing a path.")
    selected = Path(raw_path)
    if not selected.is_absolute():
        selected = _registry_root(registry_path) / selected
    return resolve_skill_dir(selected)


def _registry_root(registry_path: Path) -> Path:
    path = registry_path.resolve()
    if path.parent.name == ".skill-factory":
        return path.parent.parent
    return path.parent


def _copy_skill_tree(source: Path, destination: Path, force: bool) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise RegistryError("Export destination must be different from the source Skill directory.")
    if _is_relative_to(destination, source):
        raise RegistryError("Export destination cannot be inside the source Skill directory.")
    if destination.exists():
        if not force:
            raise RegistryError(f"Export destination already exists: {destination}")
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=_copy_ignore)


def _copy_ignore(_: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in IGNORED_DIRS or name in IGNORED_FILES or Path(name).suffix in IGNORED_SUFFIXES:
            ignored.add(name)
    return ignored


def _iter_hashable_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(skill_dir).parts)
        if parts & IGNORED_DIRS:
            continue
        if path.name in IGNORED_FILES or path.suffix in IGNORED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(skill_dir).as_posix())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
