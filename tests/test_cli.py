import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from skill_factory.cli import main
from skill_factory.llm import ProviderHealth

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


class CliTests(unittest.TestCase):
    def test_generate_manual_workflow_and_quality_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exit_code = self.run_cli(["generate", "--name", "review-data", "--brief", "Review data.",
                                         "--step", "Inspect the declared columns.", "--check", "List source rows.", "--output", tmp])
            self.assertEqual(exit_code, 0)
            text = (Path(tmp) / "review-data/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Inspect the declared columns.", text)
            self.assertIn("List source rows.", text)
            self.assertNotIn("DRAFT:", text)

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

    def test_ingest_plan_generate_and_lint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "skill-plan.json"
            skills = root / "skills"

            ingest_rc = self.run_cli(
                [
                    "ingest",
                    str(Path(__file__).parent / "fixtures" / "ingestion" / "release-workflow"),
                    "--trace",
                    str(Path(__file__).parent / "fixtures" / "ingestion" / "release.trace.json"),
                    "--name",
                    "Release Note Builder",
                    "--output",
                    str(plan_path),
                ]
            )
            generate_rc = self.run_cli(
                ["generate", "--from-plan", str(plan_path), "--output", str(skills)]
            )
            lint_rc = self.run_cli(["lint", str(skills / "release-note-builder")])

            self.assertEqual(ingest_rc, 0)
            self.assertEqual(generate_rc, 0)
            self.assertEqual(lint_rc, 0)
            self.assertTrue(
                (skills / "release-note-builder" / "references" / "sources.md").exists()
            )

    def test_eval_success_returns_zero(self) -> None:
        rc = self.run_cli(["eval", str(FIXTURES / "release-note-builder")])

        self.assertEqual(rc, 0)

    def test_eval_failure_returns_one(self) -> None:
        rc = self.run_cli(["eval", str(FIXTURES / "failing-skill"), "--no-lint"])

        self.assertEqual(rc, 1)

    def test_eval_markdown_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "eval-report.md"

            rc = self.run_cli(
                [
                    "eval",
                    str(FIXTURES / "release-note-builder"),
                    "--markdown-output",
                    str(report_path),
                ]
            )

            self.assertEqual(rc, 0)
            self.assertIn("# Skill Eval Report: PASS", report_path.read_text(encoding="utf-8"))

    def test_eval_with_baseline_skill(self) -> None:
        rc, output = self.run_cli_capture(
            [
                "eval",
                str(FIXTURES / "release-note-builder"),
                "--baseline-skill",
                str(FIXTURES / "release-note-builder"),
            ]
        )

        self.assertEqual(rc, 0)
        self.assertIn("PASS eval comparison", output)

    def test_eval_schema_outputs_json_schema(self) -> None:
        rc, output = self.run_cli_capture(["eval-schema"])

        self.assertEqual(rc, 0)
        schema = json.loads(output)
        self.assertEqual(schema["title"], "Agent Skill Factory Eval File")

    def test_trace_schema_outputs_json_schema(self) -> None:
        rc, output = self.run_cli_capture(["trace-schema"])

        self.assertEqual(rc, 0)
        schema = json.loads(output)
        self.assertEqual(schema["title"], "Agent Skill Factory Trace File")

    def test_eval_generate_writes_reviewable_eval_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "skill-plan.json"
            eval_path = root / "evals" / "evals.json"
            self.run_cli(
                [
                    "ingest",
                    str(Path(__file__).parent / "fixtures" / "ingestion" / "release-workflow"),
                    "--name",
                    "Release Note Builder",
                    "--output",
                    str(plan_path),
                ]
            )

            rc = self.run_cli(
                ["eval-generate", "--from-plan", str(plan_path), "--output", str(eval_path)]
            )

            payload = json.loads(eval_path.read_text(encoding="utf-8"))
            self.assertEqual(rc, 0)
            self.assertTrue(payload["trigger_tests"])
            self.assertTrue(payload["task_tests"])

    def test_provider_health_outputs_provider_result(self) -> None:
        client = Mock()
        client.health.return_value = ProviderHealth(
            provider="ollama",
            model="qwen3:4b",
            endpoint="http://localhost:11434/api/tags",
            reachable=True,
            model_available=True,
            detail="Configured model is available.",
        )

        with patch("skill_factory.cli.create_llm_client", return_value=client):
            rc, output = self.run_cli_capture(
                ["provider-health", "--model", "qwen3:4b", "--json"]
            )

        self.assertEqual(rc, 0)
        self.assertTrue(json.loads(output)["ok"])

    def test_eval_accepts_subprocess_runner_command(self) -> None:
        script = (
            "import json,sys; p=json.load(sys.stdin); "
            "o=p['skill']['body'] if p['use_skill'] else 'No Skill context was loaded'; "
            "print(json.dumps({'output': o}))"
        )
        command = json.dumps([sys.executable, "-c", script])

        rc = self.run_cli(
            [
                "eval",
                str(FIXTURES / "release-note-builder"),
                "--runner",
                "subprocess",
                "--runner-command",
                command,
            ]
        )

        self.assertEqual(rc, 0)

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

    def test_repair_plan_and_apply_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "repair-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: repair-skill\ndescription: \n---\n\n# Repair\n\nCreate release notes.\n",
                encoding="utf-8",
            )

            plan_rc, plan_output = self.run_cli_capture(["repair", "plan", str(skill_dir), "--json"])
            apply_rc = self.run_cli(["repair", "apply", str(skill_dir)])

            plan = json.loads(plan_output)
            self.assertEqual(plan_rc, 0)
            self.assertEqual(plan["actions"][0]["kind"], "set_description")
            self.assertEqual(apply_rc, 0)
            self.assertIn(
                "Use this skill when",
                (skill_dir / "SKILL.md").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
