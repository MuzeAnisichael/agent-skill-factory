import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from skill_factory.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


class CliTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return main(argv)

    def test_init_creates_workspace_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rc = self.run_cli(["init", tmp])

            self.assertEqual(rc, 0)
            self.assertTrue((Path(tmp) / "skill-factory.json").exists())
            self.assertTrue((Path(tmp) / "skills").is_dir())

    def test_generate_then_lint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "skills"
            generate_rc = self.run_cli(
                [
                    "generate",
                    "--name",
                    "Release Note Builder",
                    "--description",
                    "Use this skill when the agent needs to create release notes from repository changes.",
                    "--brief",
                    "Create concise release notes grounded in repository changes.",
                    "--resources",
                    "references,scripts",
                    "--output",
                    str(output),
                ]
            )
            lint_rc = self.run_cli(["lint", str(output / "release-note-builder")])

            self.assertEqual(generate_rc, 0)
            self.assertEqual(lint_rc, 0)

    def test_eval_success_returns_zero(self) -> None:
        rc = self.run_cli(["eval", str(FIXTURES / "release-note-builder")])

        self.assertEqual(rc, 0)

    def test_eval_failure_returns_one(self) -> None:
        rc = self.run_cli(["eval", str(FIXTURES / "failing-skill"), "--no-lint"])

        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
