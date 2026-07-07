from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import __version__
from .generator import RESOURCE_DIRS, create_skill
from .linter import format_report, lint_skill, report_to_json
from .models import SkillPlan
from .naming import normalize_skill_name


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

    generate_parser = subparsers.add_parser("generate", help="Generate a draft Skill package.")
    generate_parser.add_argument("--name", required=True, help="Skill name or title.")
    generate_parser.add_argument("--description", default="", help="Frontmatter description.")
    generate_parser.add_argument("--brief", default="", help="Short task or workflow brief.")
    generate_parser.add_argument("--from-file", type=Path, help="Read the brief from a text file.")
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
    generate_parser.set_defaults(func=_cmd_generate)

    lint_parser = subparsers.add_parser("lint", help="Lint one or more Skill packages.")
    lint_parser.add_argument("paths", nargs="+", type=Path, help="Skill directories or SKILL.md files.")
    lint_parser.add_argument("--json", action="store_true", help="Print JSON reports.")
    lint_parser.add_argument("--max-lines", type=int, default=500, help="Maximum SKILL.md body line count.")
    lint_parser.set_defaults(func=_cmd_lint)

    return parser


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


def _cmd_generate(args: argparse.Namespace) -> int:
    brief = args.brief
    if args.from_file:
        brief = args.from_file.read_text(encoding="utf-8")

    resources = tuple(
        item.strip()
        for item in args.resources.split(",")
        if item.strip()
    )
    invalid_resources = sorted(set(resources) - RESOURCE_DIRS)
    if invalid_resources:
        joined = ", ".join(invalid_resources)
        raise SystemExit(f"Unknown resources: {joined}. Use references,scripts,assets.")

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


def _cmd_lint(args: argparse.Namespace) -> int:
    reports = [lint_skill(path, max_lines=args.max_lines) for path in args.paths]
    if args.json:
        payload = [report.to_dict() for report in reports]
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("\n\n".join(format_report(report) for report in reports))
    return 1 if any(not report.passed for report in reports) else 0
