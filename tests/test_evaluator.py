import json
import tempfile
import unittest
from pathlib import Path

from skill_factory.evaluator import EvalError, evaluate_skill, format_eval_report

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


class EvaluatorTests(unittest.TestCase):
    def test_valid_fixture_passes_eval(self) -> None:
        report = evaluate_skill(FIXTURES / "release-note-builder")

        self.assertTrue(report.passed, report.to_dict())
        self.assertEqual(report.total_count, 3)
        self.assertEqual(report.failed_count, 0)

    def test_failing_fixture_reports_failed_assertion(self) -> None:
        report = evaluate_skill(FIXTURES / "failing-skill", include_lint=False)

        self.assertFalse(report.passed)
        self.assertEqual(report.failed_count, 1)
        self.assertIn("assertion 1 failed", report.results[0].message)

    def test_missing_eval_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "empty-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: empty-skill\ndescription: Use this skill when testing missing eval files.\n---\n\n# Empty\n",
                encoding="utf-8",
            )

            with self.assertRaises(EvalError):
                evaluate_skill(skill_dir)

    def test_invalid_trigger_schema_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill_with_eval(
                Path(tmp),
                {
                    "trigger_tests": [
                        {
                            "id": "bad-trigger",
                            "query": "Create release notes.",
                            "should_trigger": "yes"
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(EvalError, "should_trigger"):
                evaluate_skill(skill_dir)

    def test_invalid_assertion_schema_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.write_skill_with_eval(
                Path(tmp),
                {
                    "task_tests": [
                        {
                            "id": "bad-assertion",
                            "assertions": [
                                {
                                    "target": "body",
                                    "contains": "features",
                                    "not_contains": "rm -rf"
                                }
                            ]
                        }
                    ]
                },
            )

            with self.assertRaisesRegex(EvalError, "exactly one"):
                evaluate_skill(skill_dir)

    def test_report_format_includes_summary(self) -> None:
        report = evaluate_skill(FIXTURES / "release-note-builder")
        text = format_eval_report(report)

        self.assertIn("PASS", text)
        self.assertIn("Cases: 3/3 passed", text)

    def test_json_shape_is_stable(self) -> None:
        report = evaluate_skill(FIXTURES / "release-note-builder")
        payload = report.to_dict()

        self.assertEqual(payload["passed_count"], 3)
        self.assertEqual(len(payload["results"]), 3)
        json.dumps(payload)

    def write_skill_with_eval(self, root: Path, eval_payload: dict) -> Path:
        skill_dir = root / "schema-skill"
        eval_dir = skill_dir / "evals"
        eval_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            (
                "---\n"
                "name: schema-skill\n"
                "description: Use this skill when testing eval schema validation.\n"
                "---\n\n"
                "# Schema Skill\n\n"
                "Includes features and fixes.\n"
            ),
            encoding="utf-8",
        )
        (eval_dir / "evals.json").write_text(json.dumps(eval_payload), encoding="utf-8")
        return skill_dir


if __name__ == "__main__":
    unittest.main()
