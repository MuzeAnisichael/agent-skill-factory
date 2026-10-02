import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from skill_factory.evaluator import evaluate_skill
from skill_factory.generator import create_skill
from skill_factory.linter import lint_skill
from skill_factory.planner import load_skill_plan
from skill_factory.policies import load_lint_policy

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "examples/skills"
CSV_SCRIPT = SKILLS / "experiment-csv-check/scripts/check_csv.py"


class ExampleTests(unittest.TestCase):
    def test_all_examples_pass_strict_lint_and_package_evals(self) -> None:
        for path in sorted(SKILLS.iterdir()):
            with self.subTest(skill=path.name):
                report = lint_skill(path, policy=load_lint_policy("strict"))
                self.assertTrue(report.passed, report.to_dict())
                result = evaluate_skill(path)
                self.assertTrue(result.passed, result.to_dict())

    def test_reviewed_example_plan_produces_usable_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = create_skill(load_skill_plan(ROOT / "examples/plans/python-code-review.json"), Path(tmp))
            report = lint_skill(path, policy=load_lint_policy("strict"))
            self.assertTrue(report.passed, report.to_dict())
            self.assertTrue((path / "references/checklist.md").is_file())
            self.assertFalse((path / "scripts").exists())

    def test_csv_clean_input_and_read_only_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurements.csv"
            path.write_text("id,value,note\na,1.25,\nb,2.0,ok\n", encoding="utf-8")
            before = path.read_bytes()
            result = self.run_csv(path, "--required", "id", "--numeric", "value", "--unique", "id")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["empty_cell_count"], 1)
            self.assertEqual(report["issue_count"], 0)
            self.assertEqual(path.read_bytes(), before)

    def test_csv_contract_violations_include_source_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("id,value\na,NaN\na,Infinity\n,abc\nx,2,extra\n", encoding="utf-8")
            result = self.run_csv(path, "--required", "id", "--numeric", "value", "--unique", "id")
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["issue_count"], 6)
            self.assertIn({"row": 2, "column": "value", "code": "numeric.invalid"}, report["issues"])
            self.assertIn({"row": 3, "column": "id", "code": "unique.duplicate"}, report["issues"])
            self.assertIn({"row": 5, "column": "", "code": "row.width"}, report["issues"])

    def test_csv_invalid_input_returns_two(self) -> None:
        for text, args in (("", ()), ("id,id\na,b\n", ()), ("id,\na,b\n", ()),
                           ('id,value\na,"unterminated\n', ()),
                           ("id,value\na,1\n", ("--required", "missing"))):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "bad.csv"
                path.write_text(text, encoding="utf-8")
                result = self.run_csv(path, *args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("ERROR:", result.stderr)

    def test_csv_missing_file_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_csv(Path(tmp) / "missing.csv").returncode, 2)

    def test_csv_bom_custom_delimiter_and_multiline_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurements.csv"
            path.write_text('id;value;note\na;1;"first\nsecond"\nb;bad;ok\n', encoding="utf-8-sig")
            result = self.run_csv(path, "--delimiter", ";", "--numeric", "value")
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(report["row_count"], 2)
            self.assertEqual(report["issues"][0]["row"], 4)

    def test_csv_issue_display_is_bounded_but_count_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("value\n" + "not-a-number\n" * 40, encoding="utf-8")
            result = self.run_csv(path, "--numeric", "value")
            report = json.loads(result.stdout)
            self.assertEqual(report["issue_count"], 40)
            self.assertEqual(len(report["issues"]), 25)

    def run_csv(self, path: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(CSV_SCRIPT), str(path), *args],
                              capture_output=True, text=True, encoding="utf-8", timeout=10)


if __name__ == "__main__":
    unittest.main()
