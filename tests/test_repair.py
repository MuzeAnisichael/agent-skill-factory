import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from skill_factory.evaluator import evaluate_skill
from skill_factory.frontmatter import parse_frontmatter
from skill_factory.linter import lint_skill
from skill_factory.repair import apply_repairs, plan_repairs


class RepairTests(unittest.TestCase):
    def test_repair_preserves_optional_metadata_and_multiline_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "repair-skill"
            skill_dir.mkdir()
            path = skill_dir / "SKILL.md"
            path.write_text('---\nname: repair-skill\ndescription: >-\n  Review: data\n'
                            'license: MIT\nmetadata:\n  version: "1.0"\n---\n\n# Review\n\nRead source data.\n', encoding="utf-8")
            result = apply_repairs(skill_dir, include_eval=False)
            self.assertTrue(result.accepted, result.to_dict())
            parsed = parse_frontmatter(path.read_text(encoding="utf-8"))
            self.assertFalse(parsed.errors)
            self.assertEqual(parsed.data["license"], "MIT")
            self.assertEqual(parsed.data["metadata"], {"version": "1.0"})
            self.assertIn("review: data", parsed.string("description"))
            self.assertIn("Read source data.", parsed.body)

    def test_duplicate_frontmatter_requires_manual_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill(Path(tmp))
            path = skill_dir / "SKILL.md"
            text = path.read_text(encoding="utf-8").replace("name: repair-skill", "name: repair-skill\nname: other")
            path.write_text(text, encoding="utf-8")
            plan = plan_repairs(skill_dir, include_eval=False)
            self.assertTrue(plan.blocked)
            self.assertEqual(plan.actionable_count, 0)
            self.write_eval(skill_dir, {"task_tests": [{"id": "missing-term", "assertions": ["missing-term"]}],
                                       "runner_tests": [{"id": "invalid-skill", "prompt": "Check input.", "assertions": ["missing-term"]}]})
            self.assertEqual(plan_repairs(skill_dir).actionable_count, 0)
            runner = Mock()
            apply_repairs(skill_dir, runner=runner)
            runner.run.assert_not_called()
            self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_plan_repairs_missing_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill(Path(tmp), description="")

            plan = plan_repairs(skill_dir, include_eval=False)

            self.assertEqual(plan.actionable_count, 1)
            self.assertEqual(plan.actions[0].kind, "set_description")

    def test_apply_repairs_missing_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill(Path(tmp), description="")

            result = apply_repairs(skill_dir, include_eval=False)

            self.assertTrue(result.accepted, result.to_dict())
            self.assertFalse(result.rolled_back)
            self.assertTrue(lint_skill(skill_dir).passed)

    def test_apply_repairs_creates_missing_resource(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill(
                Path(tmp),
                body="Load `references/domain.md` when domain details are needed.",
            )

            result = apply_repairs(skill_dir, include_eval=False)

            self.assertTrue(result.accepted, result.to_dict())
            self.assertTrue((skill_dir / "references" / "domain.md").exists())
            self.assertTrue(lint_skill(skill_dir).passed)

    def test_apply_repairs_splits_oversized_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            body = "\n".join(f"Line {index}" for index in range(20))
            skill_dir = self.write_skill(Path(tmp), body=body)

            result = apply_repairs(skill_dir, include_eval=False, max_lines=8)

            self.assertTrue(result.accepted, result.to_dict())
            self.assertTrue((skill_dir / "references" / "overflow.md").exists())
            self.assertLessEqual(len((skill_dir / "SKILL.md").read_text(encoding="utf-8").splitlines()), 14)
            self.assertTrue(lint_skill(skill_dir, max_lines=8).passed)

    def test_apply_repairs_improves_eval_assertion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill(Path(tmp), body="Create release notes from repository changes.")
            self.write_eval(
                skill_dir,
                {
                    "task_tests": [
                        {
                            "id": "requires-features",
                            "assertions": [{"target": "body", "contains": "features"}],
                        }
                    ]
                },
            )

            before = evaluate_skill(skill_dir, include_lint=False)
            result = apply_repairs(skill_dir)
            after = evaluate_skill(skill_dir, include_lint=False)

            self.assertFalse(before.passed)
            self.assertTrue(result.accepted, result.to_dict())
            self.assertTrue(after.passed, after.to_dict())
            self.assertIn("features", (skill_dir / "SKILL.md").read_text(encoding="utf-8"))

    def test_dangerous_instruction_requires_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill(Path(tmp), body="Run rm -rf on the target directory.")

            plan = plan_repairs(skill_dir, include_eval=False)
            result = apply_repairs(skill_dir, include_eval=False)
            risky_result = apply_repairs(skill_dir, include_eval=False, allow_risky=True)

            self.assertTrue(plan.blocked)
            self.assertEqual(plan.actions[0].kind, "manual_review")
            self.assertFalse(result.accepted)
            self.assertFalse(risky_result.accepted)
            self.assertIn("rm -rf", (skill_dir / "SKILL.md").read_text(encoding="utf-8"))

    def write_skill(
        self,
        root: Path,
        description: str = (
            "Use this skill when the agent needs to create release notes from repository changes."
        ),
        body: str = "Create release notes from repository changes.",
    ) -> Path:
        skill_dir = root / "repair-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: repair-skill",
                    f"description: {description}",
                    "---",
                    "",
                    "# Repair Skill",
                    "",
                    body,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return skill_dir

    def write_eval(self, skill_dir: Path, payload: dict) -> None:
        eval_dir = skill_dir / "evals"
        eval_dir.mkdir()
        (eval_dir / "evals.json").write_text(json.dumps(payload), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
