from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from .extractors import (
    dedupe,
    extract_constraints,
    extract_examples,
    extract_summary,
    extract_terminology,
    join_brief,
)
from .models import SkillPlan, SourceReference
from .naming import display_name, normalize_skill_name
from .security import dangerous_messages
from .traces import TraceError, extract_trace_data, parse_trace


DEFAULT_MAX_FILES = 100
DEFAULT_MAX_FILE_BYTES = 1_000_000
DEFAULT_MAX_TOTAL_BYTES = 5_000_000
MAX_EXAMPLES = 20
MAX_CONSTRAINTS = 30
MAX_TERMS = 40
MAX_FAILURE_CASES = 20
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cfg",
    ".conf",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".log",
    ".md",
    ".mdx",
    ".php",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".rst",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {"Dockerfile", "Makefile", "Procfile"}


class IngestionError(ValueError):
    pass


@dataclass(frozen=True)
class _Candidate:
    path: Path
    label: str
    kind: str


@dataclass(frozen=True)
class _Document:
    reference: SourceReference
    text: str


def ingest_sources(
    source_paths: Sequence[Path],
    trace_paths: Sequence[Path] = (),
    *,
    name: str | None = None,
    description: str | None = None,
    max_files: int = DEFAULT_MAX_FILES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> SkillPlan:
    if not source_paths and not trace_paths:
        raise IngestionError("Provide at least one source path or --trace file.")
    _validate_limits(max_files, max_file_bytes, max_total_bytes)

    candidates = _collect_candidates(source_paths, trace_paths)
    if not candidates:
        raise IngestionError("No supported text source files were found.")
    if len(candidates) > max_files:
        raise IngestionError(f"Found {len(candidates)} files; --max-files is {max_files}.")

    documents: list[_Document] = []
    trace_payloads: list[tuple[SourceReference, dict[str, Any]]] = []
    review_notes: list[str] = []
    total_bytes = 0

    for candidate in candidates:
        try:
            raw = candidate.path.read_bytes()
        except OSError as exc:
            raise IngestionError(f"Could not read source file: {candidate.path}") from exc
        if len(raw) > max_file_bytes:
            raise IngestionError(
                f"Source file exceeds --max-file-bytes ({max_file_bytes}): {candidate.path}"
            )
        total_bytes += len(raw)
        if total_bytes > max_total_bytes:
            raise IngestionError(
                f"Source files exceed --max-total-bytes ({max_total_bytes})."
            )

        reference = SourceReference(
            path=candidate.label,
            sha256=hashlib.sha256(raw).hexdigest(),
            kind=candidate.kind,
            size_bytes=len(raw),
        )
        if candidate.kind == "trace":
            try:
                payload = parse_trace(_decode_text(raw, candidate.path), candidate.label)
            except TraceError as exc:
                raise IngestionError(str(exc)) from exc
            trace_payloads.append((reference, payload))
            continue

        text = _decode_text(raw, candidate.path)
        safe_text, notes = _remove_unsafe_lines(text, candidate.label)
        documents.append(_Document(reference=reference, text=safe_text))
        review_notes.extend(notes)

    examples: list[str] = []
    constraints: list[str] = []
    terminology: list[str] = []
    summaries: list[str] = []
    tool_candidates: list[str] = []
    failure_cases: list[str] = []

    for document in documents:
        examples.extend(extract_examples(document.text))
        constraints.extend(extract_constraints(document.text))
        terminology.extend(extract_terminology(document.text))
        summary = extract_summary(document.text)
        if summary:
            summaries.append(summary)

    for reference, payload in trace_payloads:
        trace_data = extract_trace_data(payload, reference.path, review_notes)
        examples.extend(trace_data["examples"])
        constraints.extend(trace_data["constraints"])
        tool_candidates.extend(trace_data["tools"])
        failure_cases.extend(trace_data["failure_cases"])
        summaries.extend(trace_data["summaries"])

    raw_name = name or _infer_name(source_paths, trace_paths)
    try:
        skill_name = normalize_skill_name(raw_name)
    except ValueError as exc:
        if name:
            raise IngestionError(str(exc)) from exc
        skill_name = "ingested-skill"
    skill_description = description.strip() if description else (
        f"Use this skill when the agent needs to apply {display_name(skill_name)} workflows grounded in "
        "indexed source material and observed task traces."
    )
    brief = join_brief(summaries)
    if not brief:
        brief = f"Apply the workflow grounded in {len(candidates)} indexed source file(s)."

    references = tuple(
        candidate_reference
        for candidate_reference in (
            [document.reference for document in documents]
            + [reference for reference, _ in trace_payloads]
        )
    )
    return SkillPlan(
        name=skill_name,
        description=skill_description,
        brief=brief,
        resources=("references",),
        examples=dedupe(examples, MAX_EXAMPLES),
        constraints=dedupe(constraints, MAX_CONSTRAINTS),
        terminology=dedupe(terminology, MAX_TERMS),
        tool_candidates=dedupe(tool_candidates, MAX_TERMS),
        failure_cases=dedupe(failure_cases, MAX_FAILURE_CASES),
        sources=references,
        review_notes=dedupe(review_notes, MAX_CONSTRAINTS),
    )


def _collect_candidates(
    source_paths: Sequence[Path], trace_paths: Sequence[Path]
) -> list[_Candidate]:
    candidates: dict[Path, _Candidate] = {}
    for source_path in source_paths:
        for candidate in _expand_source_path(source_path):
            candidates.setdefault(candidate.path.resolve(), candidate)
    for trace_path in trace_paths:
        resolved = trace_path.resolve()
        if not resolved.exists() or not resolved.is_file():
            raise IngestionError(f"Trace file does not exist: {trace_path}")
        candidates[resolved] = _Candidate(
            path=resolved,
            label=_input_label(trace_path),
            kind="trace",
        )
    ordered = sorted(
        candidates.values(),
        key=lambda item: (item.label.casefold(), item.kind, item.path.as_posix().casefold()),
    )
    return _with_unique_labels(ordered)


def _expand_source_path(source_path: Path) -> list[_Candidate]:
    resolved = source_path.resolve()
    if not resolved.exists():
        raise IngestionError(f"Source path does not exist: {source_path}")
    if resolved.is_file():
        return [_Candidate(path=resolved, label=_input_label(source_path), kind="document")]
    if not resolved.is_dir():
        raise IngestionError(f"Source path is not a file or directory: {source_path}")

    label_root = source_path.name or resolved.name
    found: list[_Candidate] = []
    for path in sorted(resolved.rglob("*"), key=lambda item: item.as_posix().casefold()):
        relative = path.relative_to(resolved)
        if any(part in IGNORED_DIRS or part.startswith(".") for part in relative.parts):
            continue
        if not path.is_file() or not _is_supported_text_file(path):
            continue
        try:
            path.resolve().relative_to(resolved)
        except ValueError:
            continue
        found.append(
            _Candidate(
                path=path,
                label=(Path(label_root) / relative).as_posix(),
                kind="document",
            )
        )
    return found


def _input_label(path: Path) -> str:
    if path.is_absolute():
        return path.name
    return path.as_posix().lstrip("./")


def _with_unique_labels(candidates: Sequence[_Candidate]) -> list[_Candidate]:
    result: list[_Candidate] = []
    used: set[str] = set()
    for candidate in candidates:
        label = candidate.label
        number = 2
        while label.casefold() in used:
            label = _numbered_label(candidate.label, number)
            number += 1
        used.add(label.casefold())
        result.append(_Candidate(path=candidate.path, label=label, kind=candidate.kind))
    return result


def _numbered_label(label: str, number: int) -> str:
    path = PurePosixPath(label)
    numbered_name = f"{path.stem}-{number}{path.suffix}"
    return (path.parent / numbered_name).as_posix()


def _is_supported_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in TEXT_FILENAMES


def _decode_text(raw: bytes, path: Path) -> str:
    if b"\x00" in raw:
        raise IngestionError(f"Source file appears to be binary: {path}")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError(f"Source file is not UTF-8 text: {path}") from exc


def _remove_unsafe_lines(text: str, label: str) -> tuple[str, list[str]]:
    safe_lines: list[str] = []
    notes: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        messages = dangerous_messages(line)
        if messages:
            notes.append(f"{label}:{line_number}: omitted {', '.join(messages)}.")
            safe_lines.append("")
        else:
            safe_lines.append(line)
    return "\n".join(safe_lines), notes


def _infer_name(source_paths: Sequence[Path], trace_paths: Sequence[Path]) -> str:
    first = next(iter(source_paths), None) or next(iter(trace_paths), None)
    if first is None:
        return "ingested-skill"
    if first.exists() and first.is_dir():
        return first.name or "ingested-skill"
    stem = first.stem
    if stem.endswith(".trace"):
        stem = stem[: -len(".trace")]
    return stem or "ingested-skill"


def _validate_limits(max_files: int, max_file_bytes: int, max_total_bytes: int) -> None:
    limits = {
        "--max-files": max_files,
        "--max-file-bytes": max_file_bytes,
        "--max-total-bytes": max_total_bytes,
    }
    for name, value in limits.items():
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise IngestionError(f"{name} must be a positive integer.")
