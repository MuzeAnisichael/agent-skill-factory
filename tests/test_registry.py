import json
import tempfile
import unittest
from pathlib import Path

from skill_factory.generator import create_skill
from skill_factory.models import SkillPlan
from skill_factory.registry import (
    RegistryError,
    export_skill,
    install_registered_skill,
    load_registry,
    register_skill,
)


class RegistryTests(unittest.TestCase):
    def test_register_skill_writes_reviewable_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = self.write_skill(root)
            registry_path = root / ".skill-factory" / "registry.json"

            entry = register_skill(
                skill_dir,
                registry_path=registry_path,
                version="0.3.0",
                include_eval=False,
            )

            self.assertEqual(entry["name"], "release-note-builder")
            self.assertEqual(entry["path"], "skills/release-note-builder")
            self.assertEqual(entry["risk"]["level"], "low")
            self.assertEqual(entry["eval"]["status"], "skipped")
            self.assertIn("package_sha256", entry["source"])
            self.assertTrue(entry["source"]["files"])

            payload = load_registry(registry_path)
            self.assertIn("release-note-builder", payload["skills"])
            json.dumps(payload)

    def test_register_refuses_lint_errors_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "bad-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: bad-skill\ndescription: \n---\n\n# Bad\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RegistryError, "lint errors"):
                register_skill(skill_dir, registry_path=root / ".skill-factory" / "registry.json")

    def test_export_skill_copies_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = self.write_skill(root)

            destination = export_skill(skill_dir, output_dir=root / "exports")

            expected = root / "exports" / "release-note-builder"
            self.assertTrue(destination.samefile(expected))
            self.assertTrue((destination / "SKILL.md").exists())
            self.assertTrue((destination / "agents" / "openai.yaml").exists())

    def test_install_registered_skill_uses_registry_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = self.write_skill(root)
            registry_path = root / ".skill-factory" / "registry.json"
            register_skill(skill_dir, registry_path=registry_path, include_eval=False)

            destination = install_registered_skill(
                "release-note-builder",
                registry_path=registry_path,
                output_dir=root / "installed",
            )

            self.assertTrue((destination / "SKILL.md").exists())

    def write_skill(self, root: Path) -> Path:
        return create_skill(
            SkillPlan(
                name="release-note-builder",
                description=(
                    "Use this skill when the agent needs to create release notes from "
                    "repository changes, merged pull requests, or changelog source material."
                ),
                brief="Create concise release notes grounded in repository changes.",
                resources=("references", "scripts"),
                examples=("Create release notes for the current branch.",),
            ),
            root / "skills",
        )


if __name__ == "__main__":
    unittest.main()
