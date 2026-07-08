import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from skill_factory.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


class CliTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return main(argv)

    def run_cli_capture(self, argv: list[str]) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main(argv)
        return rc, output.getvalue()

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

    def test_eval_schema_outputs_json_schema(self) -> None:
        rc, output = self.run_cli_capture(["eval-schema"])

        self.assertEqual(rc, 0)
        schema = json.loads(output)
        self.assertEqual(schema["title"], "Agent Skill Factory Eval File")

    def test_registry_add_list_and_install_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "skills"
            registry_path = root / ".skill-factory" / "registry.json"
            installed = root / "installed"
            self.run_cli(
                [
                    "generate",
                    "--name",
                    "Release Note Builder",
                    "--description",
                    "Use this skill when the agent needs to create release notes from repository changes.",
                    "--brief",
                    "Create concise release notes grounded in repository changes.",
                    "--resources",
                    "references",
                    "--output",
                    str(output),
                ]
            )

            add_rc = self.run_cli(
                [
                    "registry",
                    "add",
                    str(output / "release-note-builder"),
                    "--registry",
                    str(registry_path),
                    "--skip-eval",
                ]
            )
            list_rc, list_output = self.run_cli_capture(
                ["registry", "list", "--registry", str(registry_path)]
            )
            install_rc = self.run_cli(
                [
                    "install",
                    "release-note-builder",
                    "--registry",
                    str(registry_path),
                    "--output",
                    str(installed),
                ]
            )

            self.assertEqual(add_rc, 0)
            self.assertEqual(list_rc, 0)
            self.assertIn("release-note-builder", list_output)
            self.assertEqual(install_rc, 0)
            self.assertTrue((installed / "release-note-builder" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
