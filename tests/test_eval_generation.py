import json
import tempfile
import unittest
from pathlib import Path

from skill_factory.eval_generation import generate_eval_payload
from skill_factory.evaluator import evaluate_skill
from skill_factory.generator import create_skill
from skill_factory.models import SkillPlan


class EvalGenerationTests(unittest.TestCase):
    def test_generated_eval_uses_examples_failures_and_constraints(self) -> None:
        plan = SkillPlan(
            name="release-note-builder",
            description=(
                "Use this skill when creating release notes from repository changes and pull requests."
            ),
            brief="Create concise release notes grounded in repository changes.",
            examples=("Create release notes for the current branch.",),
            constraints=("Group entries under Features and Fixes.",),
            terminology=("release notes",),
            failure_cases=("Summarize merged changes: Missing pull request metadata",),
        )

        payload = generate_eval_payload(plan)

        self.assertEqual(len(payload["trigger_tests"]), 2)
        self.assertEqual(payload["trigger_tests"][1]["query"], "Summarize merged changes")
        self.assertEqual(
            payload["task_tests"][0]["assertions"][0]["all_contains"],
            ["Group entries under Features and Fixes."],
        )

    def test_generated_eval_runs_against_generated_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = SkillPlan(
                name="release-note-builder",
                description=(
                    "Use this skill when creating release notes from repository changes and pull requests."
                ),
                brief="Create concise release notes grounded in repository changes.",
                examples=("Create release notes for the current branch.",),
                constraints=("Group entries under Features and Fixes.",),
            )
            skill_dir = create_skill(plan, root)
            eval_dir = skill_dir / "evals"
            eval_dir.mkdir()
            (eval_dir / "evals.json").write_text(
                json.dumps(generate_eval_payload(plan)), encoding="utf-8"
            )

            report = evaluate_skill(skill_dir)

            self.assertTrue(report.passed, report.to_dict())


if __name__ == "__main__":
    unittest.main()
