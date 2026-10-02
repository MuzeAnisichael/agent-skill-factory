import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from skill_factory.frontmatter import parse_frontmatter, render_frontmatter
from skill_factory.generator import create_skill
from skill_factory.linter import lint_skill
from skill_factory.models import ResourceFile, SkillPlan
from skill_factory.planner import load_skill_plan, skill_plan_to_dict
from skill_factory.policies import load_lint_policy


class GenerationQualityTests(unittest.TestCase):
    def test_exact_specification_limits_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            name = "a" * 64
            skill_dir = Path(tmp) / name
            skill_dir.mkdir()
            data = {"name": name, "description": "Use when " + "x" * 1015, "compatibility": "x" * 500}
            (skill_dir / "SKILL.md").write_text(render_frontmatter(data, "Inspect input."), encoding="utf-8")
            report = lint_skill(skill_dir, policy=load_lint_policy("strict"))
            self.assertTrue(report.passed, report.to_dict())

    def test_resource_content_whitespace_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content = "field  \n\n"
            skill_dir = create_skill(SkillPlan("a", "", "Check.",
                                              resource_files=(ResourceFile("assets/template.txt", content, "Output contract."),)), Path(tmp))
            self.assertEqual((skill_dir / "assets/template.txt").read_text(encoding="utf-8"), content)
            interface = yaml.safe_load((skill_dir / "agents/openai.yaml").read_text(encoding="utf-8"))["interface"]
            self.assertGreaterEqual(len(interface["short_description"]), 25)

    def test_force_conflict_preserves_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "sample"
            (skill_dir / "references/contract.md").mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("unchanged", encoding="utf-8")
            plan = SkillPlan("sample", "Use when checking data.", "Check.",
                             resource_files=(ResourceFile("references/contract.md", "content", "Read it."),))
            with self.assertRaises(ValueError):
                create_skill(plan, root, force=True)
            self.assertEqual((skill_dir / "SKILL.md").read_text(encoding="utf-8"), "unchanged")

    def test_symlink_preflight_branch_without_os_privileges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("skill_factory.generator.Path.is_symlink", autospec=True,
                       side_effect=lambda path: path.name == "SKILL.md"):
                with self.assertRaises(ValueError):
                    create_skill(SkillPlan("sample", "Use when checking paths.", "Check."), root)
            self.assertFalse((root / "sample").exists())

    def test_old_placeholder_resources_fail_strict_lint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_skill(SkillPlan("sample", "Use when reviewing declared input contracts before processing experimental data.",
                                          "Review.", workflow=("Inspect the source inputs.",), resources=("scripts",)), Path(tmp))
            (path / "scripts/helper.py").write_text('print("Replace this placeholder with a real operation.")\n', encoding="utf-8")
            report = lint_skill(path, policy=load_lint_policy("strict"))
            self.assertFalse(report.passed)
            self.assertIn("resource.unfinished", {item.code for item in report.findings})

    def test_reviewed_plan_round_trip_and_render(self) -> None:
        plan = SkillPlan(
            name="csv-review", description='用于检查实验 CSV 数据: 缺失值、重复记录和非有限数值，在统计分析前提供可复核的证据。',
            brief="Check the declared CSV input contract.", workflow=("Read the declared columns.", "Inspect each row."),
            quality_checks=("Every finding includes its source row.",),
            resource_files=(ResourceFile("references/contract.md", "ID must be unique.\n", "Read before checking IDs."),),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(skill_plan_to_dict(plan)), encoding="utf-8")
            loaded = load_skill_plan(plan_path)
            self.assertEqual(loaded, plan)
            skill_dir = create_skill(loaded, root)
            parsed = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(parsed.string("description"), plan.description)
            self.assertIn("1. Read the declared columns.", parsed.body)
            self.assertIn("Every finding includes its source row.", parsed.body)
            self.assertEqual((skill_dir / "references/contract.md").read_text(encoding="utf-8"), "ID must be unique.\n")
            self.assertTrue(lint_skill(skill_dir, policy=load_lint_policy("strict")).passed)
            interface = yaml.safe_load((skill_dir / "agents/openai.yaml").read_text(encoding="utf-8"))["interface"]
            self.assertIn("$csv-review", interface["default_prompt"])
            self.assertLessEqual(len(interface["short_description"]), 64)
            self.assertGreaterEqual(len(interface["short_description"]), 25)

    def test_legacy_plan_remains_readable_but_is_a_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "plan.json"
            path.write_text(json.dumps({"schema_version": 1, "name": "old-skill", "description": "Use when checking old inputs.",
                                       "brief": "Inspect input.", "resources": ["scripts", "assets"]}), encoding="utf-8")
            skill_dir = create_skill(load_skill_plan(path), root)
            self.assertFalse(list((skill_dir / "scripts").iterdir()))
            self.assertIn("body.unfinished", {item.code for item in lint_skill(skill_dir).findings})
            self.assertFalse(lint_skill(skill_dir, policy=load_lint_policy("strict")).passed)

    def test_invalid_resource_paths_fail_before_writing(self) -> None:
        for path in ("../outside.txt", "scripts/../../outside.py", "scripts\\helper.py", "/scripts/a.py",
                     "SKILL.md", "scripts/CON.py", "scripts/a.", "scripts/./a.py", "scripts//a.py"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with self.assertRaises(ValueError):
                    create_skill(SkillPlan("sample", "Use when checking resources.", "Check.",
                                           resource_files=(ResourceFile(path, "content", "Use it."),)), root)
                self.assertFalse((root / "sample").exists())

    def test_duplicate_and_file_directory_conflicts_fail_before_writing(self) -> None:
        for paths in (("scripts/a.py", "scripts/A.py"), ("scripts/a", "scripts/a/b.py")):
            with self.subTest(paths=paths), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with self.assertRaises(ValueError):
                    create_skill(SkillPlan("sample", "Use when checking resources.", "Check.",
                                           resource_files=tuple(ResourceFile(p, "content", "Use it.") for p in paths)), root)
                self.assertFalse((root / "sample").exists())

    def test_invalid_new_plan_fields_are_rejected(self) -> None:
        for field in ({"workflow": "not an array"}, {"workflow": [""]}, {"quality_checks": [False]},
                      {"resource_files": {}}, {"resource_files": [{"path": "scripts/a.py", "content": ""}]},
                      {"resource_files": [{"path": "../bad.py", "content": "x", "purpose": "x"}]}):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "plan.json"
                path.write_text(json.dumps({"name": "sample", "description": "Use when checking data.", "brief": "Check.", **field}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_skill_plan(path)

    def test_symlink_overwrite_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside.md"
            outside.write_text("unchanged", encoding="utf-8")
            (root / "sample").mkdir()
            try:
                (root / "sample/SKILL.md").symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"Symlink creation unavailable: {exc}")
            with self.assertRaises(ValueError):
                create_skill(SkillPlan("sample", "Use when testing symlinks.", "Test."), root, force=True)
            self.assertEqual(outside.read_text(encoding="utf-8"), "unchanged")

    def test_valid_optional_metadata_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "sample"
            skill_dir.mkdir()
            data = {"name": "sample", "description": "Use when reviewing experimental CSV data and checking its explicitly declared input contract before analysis.",
                    "license": "MIT", "compatibility": "Python 3.10+", "metadata": {"author": "team", "version": "1.0"},
                    "allowed-tools": "Read"}
            (skill_dir / "SKILL.md").write_text(render_frontmatter(data, "Read the declared contract."), encoding="utf-8")
            self.assertTrue(lint_skill(skill_dir, policy=load_lint_policy("strict")).passed)

    def test_invalid_metadata_types_and_limits_fail_without_crashing(self) -> None:
        cases = ({"name": 4}, {"description": ["wrong"]}, {"description": "x" * 1025},
                 {"metadata": {"version": 1}}, {"metadata": []}, {"compatibility": "x" * 501},
                 {"license": False}, {"allowed-tools": ["Read"]}, {"name": "sample--skill"})
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "sample"
            skill_dir.mkdir()
            for changes in cases:
                with self.subTest(changes=changes):
                    data = {"name": "sample", "description": "Use when validating metadata types and exact length limits.", **changes}
                    (skill_dir / "SKILL.md").write_text(render_frontmatter(data, "Read inputs."), encoding="utf-8")
                    self.assertFalse(lint_skill(skill_dir).passed)


if __name__ == "__main__":
    unittest.main()
