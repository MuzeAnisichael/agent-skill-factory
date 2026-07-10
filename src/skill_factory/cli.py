from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import __version__
from .evaluator import (
    EvalError,
    compare_eval_reports,
    eval_comparison_to_json,
    eval_report_to_json,
    evaluate_skill,
    format_eval_comparison,
    format_eval_comparison_markdown,
    format_eval_report,
    format_eval_report_markdown,
)
from .generator import RESOURCE_DIRS, create_skill
from .ingestion import (
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_TOTAL_BYTES,
    IngestionError,
    ingest_sources,
)
from .linter import format_report, lint_skill, report_to_json
from .llm import LLMError, create_llm_client
from .models import SkillPlan
from .naming import normalize_skill_name
from .planner import load_skill_plan, plan_skill_with_llm, skill_plan_to_dict
from .registry import (
    DEFAULT_REGISTRY_PATH,
    EXPORT_TARGETS,
    RegistryError,
    export_skill,
    format_registry_list,
    install_registered_skill,
    list_registry_entries,
    load_registry,
    register_skill,
)
from .repair import (
    RepairError,
    apply_repairs,
    format_repair_plan,
    format_repair_result,
    plan_repairs,
    repair_plan_to_json,
    repair_result_to_json,
)
from .runner import DryRunRunner, LLMEvalRunner
from .schemas import eval_schema_json, trace_schema_json


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-factory",
        description="Generate, lint, and manage reusable Agent Skills.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a local Skill Factory workspace.")
    init_parser.add_argument("path", nargs="?", default=".", help="Workspace path.")
    init_parser.add_argument("--skills-dir", default="skills", help="Directory for generated Skills.")
    init_parser.set_defaults(func=_cmd_init)

    ingest_parser = subparsers.add_parser(
        "ingest", help="Create a reviewable SkillPlan from local sources and Agent traces."
    )
    ingest_parser.add_argument("sources", nargs="*", type=Path, help="Text files or directories.")
    ingest_parser.add_argument(
        "--trace",
        action="append",
        type=Path,
        default=[],
        help="Agent trace JSON file. Can be repeated.",
    )
    ingest_parser.add_argument("--name", help="Preferred Skill name. Defaults to the first source name.")
    ingest_parser.add_argument("--description", help="Preferred frontmatter description.")
    ingest_parser.add_argument("--output", type=Path, help="Write SkillPlan JSON instead of printing it.")
    ingest_parser.add_argument(
        "--max-files", type=int, default=DEFAULT_MAX_FILES, help="Maximum number of indexed files."
    )
    ingest_parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=DEFAULT_MAX_FILE_BYTES,
        help="Maximum bytes per source file.",
    )
    ingest_parser.add_argument(
        "--max-total-bytes",
        type=int,
        default=DEFAULT_MAX_TOTAL_BYTES,
        help="Maximum bytes across all source files.",
    )
    ingest_parser.set_defaults(func=_cmd_ingest)

    generate_parser = subparsers.add_parser("generate", help="Generate a draft Skill package.")
    generate_parser.add_argument("--name", help="Skill name or title.")
    generate_parser.add_argument("--description", default="", help="Frontmatter description.")
    generate_parser.add_argument("--brief", default="", help="Short task or workflow brief.")
    generate_parser.add_argument("--from-file", type=Path, help="Read the brief from a text file.")
    generate_parser.add_argument(
        "--from-plan",
        type=Path,
        help="Generate from a reviewed SkillPlan JSON file.",
    )
    generate_parser.add_argument(
        "--resources",
        default="",
        help="Comma-separated resource directories: references,scripts,assets.",
    )
    generate_parser.add_argument(
        "--example",
        action="append",
        default=[],
        help="Concrete user request that should use the Skill. Can be repeated.",
    )
    generate_parser.add_argument("--output", type=Path, default=Path("skills"), help="Output directory.")
    generate_parser.add_argument("--force", action="store_true", help="Overwrite an existing Skill folder.")
    generate_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use an LLM provider to create the SkillPlan before writing files.",
    )
    _add_llm_args(generate_parser)
    generate_parser.set_defaults(func=_cmd_generate)

    plan_parser = subparsers.add_parser("plan", help="Use an LLM provider to create a SkillPlan JSON object.")
    plan_parser.add_argument("--name", help="Optional preferred Skill name.")
    plan_parser.add_argument("--description", default="", help="Optional preferred frontmatter description.")
    plan_parser.add_argument("--brief", default="", help="Short task or workflow brief.")
    plan_parser.add_argument("--from-file", type=Path, help="Read the brief from a text file.")
    plan_parser.add_argument(
        "--resources",
        default="",
        help="Comma-separated preferred resource directories: references,scripts,assets.",
    )
    plan_parser.add_argument(
        "--example",
        action="append",
        default=[],
        help="Concrete user request that should use the Skill. Can be repeated.",
    )
    _add_llm_args(plan_parser)
    plan_parser.set_defaults(func=_cmd_plan)

    lint_parser = subparsers.add_parser("lint", help="Lint one or more Skill packages.")
    lint_parser.add_argument("paths", nargs="+", type=Path, help="Skill directories or SKILL.md files.")
    lint_parser.add_argument("--json", action="store_true", help="Print JSON reports.")
    lint_parser.add_argument("--max-lines", type=int, default=500, help="Maximum SKILL.md body line count.")
    lint_parser.set_defaults(func=_cmd_lint)

    eval_parser = subparsers.add_parser("eval", help="Run local evals for a Skill package.")
    eval_parser.add_argument("skill", type=Path, help="Skill directory or SKILL.md file.")
    eval_parser.add_argument(
        "--eval-file",
        type=Path,
        help="Eval JSON file. Defaults to <skill>/evals/evals.json.",
    )
    eval_parser.add_argument("--json", action="store_true", help="Print a JSON eval report.")
    eval_parser.add_argument("--markdown", action="store_true", help="Print a Markdown eval report.")
    eval_parser.add_argument("--markdown-output", type=Path, help="Write a Markdown eval report to a file.")
    eval_parser.add_argument("--no-lint", action="store_true", help="Skip lint aggregation during eval.")
    eval_parser.add_argument(
        "--runner",
        choices=("dry-run", "llm"),
        default="dry-run",
        help="Runner for runner_tests. Defaults to deterministic dry-run.",
    )
    eval_parser.add_argument(
        "--baseline-skill",
        type=Path,
        help="Evaluate a baseline Skill and fail if the candidate regresses.",
    )
    _add_llm_args(eval_parser)
    eval_parser.set_defaults(func=_cmd_eval)

    registry_parser = subparsers.add_parser("registry", help="Manage the local Skill registry.")
    registry_subparsers = registry_parser.add_subparsers(required=True)

    registry_add_parser = registry_subparsers.add_parser("add", help="Add or update a Skill registry entry.")
    registry_add_parser.add_argument("skill", type=Path, help="Skill directory or SKILL.md file.")
    registry_add_parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="Registry JSON path. Defaults to .skill-factory/registry.json.",
    )
    registry_add_parser.add_argument("--version", default="0.1.0", help="Skill version to record.")
    registry_add_parser.add_argument("--skip-eval", action="store_true", help="Do not inspect eval results.")
    registry_add_parser.add_argument(
        "--allow-failing",
        action="store_true",
        help="Register even when lint or eval checks fail.",
    )
    registry_add_parser.add_argument("--json", action="store_true", help="Print the registered entry as JSON.")
    registry_add_parser.set_defaults(func=_cmd_registry_add)

    registry_list_parser = registry_subparsers.add_parser("list", help="List registered Skills.")
    registry_list_parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="Registry JSON path. Defaults to .skill-factory/registry.json.",
    )
    registry_list_parser.add_argument("--json", action="store_true", help="Print registry entries as JSON.")
    registry_list_parser.set_defaults(func=_cmd_registry_list)

    registry_show_parser = registry_subparsers.add_parser("show", help="Show one registered Skill.")
    registry_show_parser.add_argument("name", help="Registered Skill name.")
    registry_show_parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="Registry JSON path. Defaults to .skill-factory/registry.json.",
    )
    registry_show_parser.add_argument("--json", action="store_true", help="Print the entry as JSON.")
    registry_show_parser.set_defaults(func=_cmd_registry_show)

    export_parser = subparsers.add_parser("export", help="Export a Skill package to a client directory.")
    export_parser.add_argument("skill", type=Path, help="Skill directory or SKILL.md file.")
    export_parser.add_argument(
        "--target",
        choices=EXPORT_TARGETS,
        default="agent-skills",
        help="Client layout target.",
    )
    export_parser.add_argument("--output", type=Path, help="Destination skills directory.")
    export_parser.add_argument("--force", action="store_true", help="Overwrite an existing exported Skill.")
    export_parser.add_argument("--json", action="store_true", help="Print export result as JSON.")
    export_parser.set_defaults(func=_cmd_export)

    install_parser = subparsers.add_parser("install", help="Install a registered Skill to a client directory.")
    install_parser.add_argument("name", help="Registered Skill name.")
    install_parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="Registry JSON path. Defaults to .skill-factory/registry.json.",
    )
    install_parser.add_argument(
        "--target",
        choices=EXPORT_TARGETS,
        default="agent-skills",
        help="Client layout target.",
    )
    install_parser.add_argument("--output", type=Path, help="Destination skills directory.")
    install_parser.add_argument("--force", action="store_true", help="Overwrite an existing installed Skill.")
    install_parser.add_argument("--json", action="store_true", help="Print install result as JSON.")
    install_parser.set_defaults(func=_cmd_install)

    repair_parser = subparsers.add_parser("repair", help="Plan or apply bounded Skill repairs.")
    repair_subparsers = repair_parser.add_subparsers(required=True)

    repair_plan_parser = repair_subparsers.add_parser("plan", help="Create a repair plan without editing files.")
    repair_plan_parser.add_argument("skill", type=Path, help="Skill directory or SKILL.md file.")
    repair_plan_parser.add_argument("--eval-file", type=Path, help="Eval JSON file.")
    repair_plan_parser.add_argument("--no-eval", action="store_true", help="Skip eval-driven repair planning.")
    repair_plan_parser.add_argument("--max-lines", type=int, default=500, help="Maximum SKILL.md body line count.")
    repair_plan_parser.add_argument("--json", action="store_true", help="Print the repair plan as JSON.")
    _add_eval_runner_args(repair_plan_parser)
    repair_plan_parser.set_defaults(func=_cmd_repair_plan)

    repair_apply_parser = repair_subparsers.add_parser("apply", help="Apply safe bounded repairs and re-run checks.")
    repair_apply_parser.add_argument("skill", type=Path, help="Skill directory or SKILL.md file.")
    repair_apply_parser.add_argument("--eval-file", type=Path, help="Eval JSON file.")
    repair_apply_parser.add_argument("--no-eval", action="store_true", help="Skip eval checks during repair.")
    repair_apply_parser.add_argument("--max-lines", type=int, default=500, help="Maximum SKILL.md body line count.")
    repair_apply_parser.add_argument("--allow-risky", action="store_true", help="Allow risky repair actions.")
    repair_apply_parser.add_argument("--dry-run", action="store_true", help="Plan repair without editing files.")
    repair_apply_parser.add_argument("--json", action="store_true", help="Print the repair result as JSON.")
    _add_eval_runner_args(repair_apply_parser)
    repair_apply_parser.set_defaults(func=_cmd_repair_apply)

    eval_schema_parser = subparsers.add_parser("eval-schema", help="Print or write the eval JSON Schema.")
    eval_schema_parser.add_argument("--output", type=Path, help="Write the schema to a file instead of stdout.")
    eval_schema_parser.set_defaults(func=_cmd_eval_schema)

    trace_schema_parser = subparsers.add_parser(
        "trace-schema", help="Print or write the Agent trace JSON Schema."
    )
    trace_schema_parser.add_argument("--output", type=Path, help="Write the schema instead of stdout.")
    trace_schema_parser.set_defaults(func=_cmd_trace_schema)

    return parser


def _add_llm_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider",
        choices=("ollama", "openai-compatible", "openai", "api"),
        default="ollama",
        help="LLM provider. Defaults to local Ollama.",
    )
    parser.add_argument("--model", help="Model name. Defaults to OLLAMA_MODEL or llama3.1 for Ollama.")
    parser.add_argument("--api-base", help="Provider base URL.")
    parser.add_argument("--api-key", help="API key for OpenAI-compatible providers.")
    parser.add_argument("--timeout", type=float, default=60.0, help="LLM request timeout in seconds.")


def _add_eval_runner_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--runner",
        choices=("dry-run", "llm"),
        default="dry-run",
        help="Runner for eval-driven repair planning. Defaults to deterministic dry-run.",
    )
    _add_llm_args(parser)


def _cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path)
    skills_dir = root / args.skills_dir
    root.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    config_path = root / "skill-factory.json"
    if not config_path.exists():
        config = {"skills_dir": args.skills_dir, "version": 1}
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Initialized Skill Factory workspace at {root.resolve()}")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    try:
        plan = ingest_sources(
            source_paths=args.sources,
            trace_paths=args.trace,
            name=args.name,
            description=args.description,
            max_files=args.max_files,
            max_file_bytes=args.max_file_bytes,
            max_total_bytes=args.max_total_bytes,
        )
    except IngestionError as exc:
        raise SystemExit(str(exc)) from exc

    payload = json.dumps(skill_plan_to_dict(plan), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote SkillPlan to {args.output}")
    else:
        print(payload, end="")
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    if args.from_plan:
        if _has_plan_input_conflicts(args):
            raise SystemExit(
                "--from-plan cannot be combined with manual or LLM planning options."
            )
        try:
            plan = load_skill_plan(args.from_plan)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    else:
        brief = _read_brief(args)
        resources = _parse_resources(args.resources)
        if args.llm:
            plan = _create_llm_plan(args, brief, resources)
        else:
            if not args.name:
                raise SystemExit("--name is required unless --llm or --from-plan is used.")
            skill_name = normalize_skill_name(args.name)
            description = args.description.strip() or (
                f"Use this skill when the agent needs to complete {skill_name} tasks with a reusable workflow."
            )
            plan = SkillPlan(
                name=skill_name,
                description=description,
                brief=brief,
                resources=resources,
                examples=tuple(args.example),
            )
    skill_dir = create_skill(plan, args.output, force=args.force)
    print(f"Generated Skill at {skill_dir.resolve()}")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    brief = _read_brief(args)
    resources = _parse_resources(args.resources)
    plan = _create_llm_plan(args, brief, resources)
    print(json.dumps(skill_plan_to_dict(plan), indent=2, sort_keys=True))
    return 0


def _cmd_lint(args: argparse.Namespace) -> int:
    reports = [lint_skill(path, max_lines=args.max_lines) for path in args.paths]
    if args.json:
        payload = [report.to_dict() for report in reports]
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("\n\n".join(format_report(report) for report in reports))
    return 1 if any(not report.passed for report in reports) else 0


def _cmd_eval(args: argparse.Namespace) -> int:
    runner = _create_eval_runner(args)
    try:
        report = evaluate_skill(
            skill_path=args.skill,
            eval_path=args.eval_file,
            include_lint=not args.no_lint,
            runner=runner,
        )
        comparison = None
        if args.baseline_skill:
            baseline_report = evaluate_skill(
                skill_path=args.baseline_skill,
                eval_path=args.eval_file or _default_eval_path_for(args.skill),
                include_lint=False,
                runner=runner,
            )
            comparison = compare_eval_reports(report, baseline_report)
    except EvalError as exc:
        raise SystemExit(str(exc)) from exc

    if comparison:
        if args.json:
            print(eval_comparison_to_json(comparison))
        elif args.markdown or args.markdown_output:
            markdown = format_eval_comparison_markdown(comparison)
            _write_or_print_markdown(markdown, args.markdown_output)
        else:
            print(format_eval_comparison(comparison))
        return 0 if comparison.passed else 1

    if args.json:
        print(eval_report_to_json(report))
    elif args.markdown or args.markdown_output:
        markdown = format_eval_report_markdown(report)
        _write_or_print_markdown(markdown, args.markdown_output)
    else:
        print(format_eval_report(report))
    return 0 if report.passed else 1


def _cmd_registry_add(args: argparse.Namespace) -> int:
    try:
        entry = register_skill(
            skill_path=args.skill,
            registry_path=args.registry,
            version=args.version,
            include_eval=not args.skip_eval,
            allow_failing=args.allow_failing,
        )
    except RegistryError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps(entry, indent=2, sort_keys=True))
    else:
        print(f"Registered {entry['name']} {entry['version']} in {args.registry}")
    return 0


def _cmd_registry_list(args: argparse.Namespace) -> int:
    try:
        registry = load_registry(args.registry)
    except RegistryError as exc:
        raise SystemExit(str(exc)) from exc

    entries = list_registry_entries(registry)
    if args.json:
        print(json.dumps(entries, indent=2, sort_keys=True))
    else:
        print(format_registry_list(entries))
    return 0


def _cmd_registry_show(args: argparse.Namespace) -> int:
    try:
        registry = load_registry(args.registry)
    except RegistryError as exc:
        raise SystemExit(str(exc)) from exc

    entry = registry.get("skills", {}).get(args.name)
    if not entry:
        raise SystemExit(f"Skill is not registered: {args.name}")
    if args.json:
        print(json.dumps(entry, indent=2, sort_keys=True))
    else:
        print(format_registry_list([entry]))
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    try:
        destination = export_skill(
            skill_path=args.skill,
            output_dir=args.output,
            target=args.target,
            force=args.force,
        )
    except RegistryError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps({"path": str(destination), "target": args.target}, indent=2, sort_keys=True))
    else:
        print(f"Exported Skill to {destination}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    try:
        destination = install_registered_skill(
            name=args.name,
            registry_path=args.registry,
            output_dir=args.output,
            target=args.target,
            force=args.force,
        )
    except RegistryError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(json.dumps({"path": str(destination), "target": args.target}, indent=2, sort_keys=True))
    else:
        print(f"Installed Skill to {destination}")
    return 0


def _cmd_repair_plan(args: argparse.Namespace) -> int:
    runner = _create_eval_runner(args)
    try:
        plan = plan_repairs(
            skill_path=args.skill,
            eval_path=args.eval_file,
            max_lines=args.max_lines,
            include_eval=not args.no_eval,
            runner=runner,
        )
    except RepairError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(repair_plan_to_json(plan))
    else:
        print(format_repair_plan(plan))
    return 0


def _cmd_repair_apply(args: argparse.Namespace) -> int:
    runner = _create_eval_runner(args)
    try:
        result = apply_repairs(
            skill_path=args.skill,
            eval_path=args.eval_file,
            max_lines=args.max_lines,
            include_eval=not args.no_eval,
            runner=runner,
            allow_risky=args.allow_risky,
            dry_run=args.dry_run,
        )
    except RepairError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(repair_result_to_json(result))
    else:
        print(format_repair_result(result))
    return 0 if result.accepted else 1


def _cmd_eval_schema(args: argparse.Namespace) -> int:
    schema = eval_schema_json()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(schema, encoding="utf-8")
        print(f"Wrote eval schema to {args.output}")
    else:
        print(schema, end="")
    return 0


def _cmd_trace_schema(args: argparse.Namespace) -> int:
    schema = trace_schema_json()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(schema, encoding="utf-8")
        print(f"Wrote trace schema to {args.output}")
    else:
        print(schema, end="")
    return 0


def _create_eval_runner(args: argparse.Namespace) -> DryRunRunner | LLMEvalRunner:
    if args.runner == "dry-run":
        return DryRunRunner()
    try:
        client = create_llm_client(
            provider=args.provider,
            model=args.model,
            api_base=args.api_base,
            api_key=args.api_key,
            timeout=args.timeout,
        )
        return LLMEvalRunner(client)
    except LLMError as exc:
        raise SystemExit(str(exc)) from exc


def _default_eval_path_for(skill_path: Path) -> Path:
    skill_dir = skill_path.resolve()
    if skill_dir.is_file() and skill_dir.name == "SKILL.md":
        skill_dir = skill_dir.parent
    return skill_dir / "evals" / "evals.json"


def _write_or_print_markdown(markdown: str, output_path: Path | None) -> None:
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote eval report to {output_path}")
    else:
        print(markdown, end="")


def _read_brief(args: argparse.Namespace) -> str:
    if args.from_file:
        return args.from_file.read_text(encoding="utf-8")
    return args.brief


def _parse_resources(raw: str) -> tuple[str, ...]:
    resources = tuple(item.strip() for item in raw.split(",") if item.strip())
    invalid_resources = sorted(set(resources) - RESOURCE_DIRS)
    if invalid_resources:
        joined = ", ".join(invalid_resources)
        raise SystemExit(f"Unknown resources: {joined}. Use references,scripts,assets.")
    return resources


def _has_plan_input_conflicts(args: argparse.Namespace) -> bool:
    return bool(
        args.name
        or args.description
        or args.brief
        or args.from_file
        or args.resources
        or args.example
        or args.llm
        or args.model
        or args.api_base
        or args.api_key
        or args.provider != "ollama"
        or args.timeout != 60.0
    )


def _create_llm_plan(
    args: argparse.Namespace,
    brief: str,
    resources: tuple[str, ...],
) -> SkillPlan:
    try:
        client = create_llm_client(
            provider=args.provider,
            model=args.model,
            api_base=args.api_base,
            api_key=args.api_key,
            timeout=args.timeout,
        )
        return plan_skill_with_llm(
            client=client,
            brief=brief,
            name=args.name,
            description=args.description.strip() or None,
            resources=resources,
            examples=tuple(args.example),
        )
    except (LLMError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
