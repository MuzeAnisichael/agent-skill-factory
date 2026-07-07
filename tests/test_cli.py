import tempfile
import unittest
from pathlib import Path

from skill_factory.cli import main


class CliTests(unittest.TestCase):
    def test_init_creates_workspace_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rc = main(["init", tmp])

            self.assertEqual(rc, 0)
            self.assertTrue((Path(tmp) / "skill-factory.json").exists())
            self.assertTrue((Path(tmp) / "skills").is_dir())

    def test_generate_then_lint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "skills"
            generate_rc = main(
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
            lint_rc = main(["lint", str(output / "release-note-builder")])

            self.assertEqual(generate_rc, 0)
            self.assertEqual(lint_rc, 0)


if __name__ == "__main__":
    unittest.main()
