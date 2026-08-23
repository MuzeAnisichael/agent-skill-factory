import json
import tempfile
import unittest
from pathlib import Path

from skill_factory.linter import lint_skill
from skill_factory.policies import load_lint_policy


class LintPolicyTests(unittest.TestCase):
    def test_strict_policy_promotes_warnings_to_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "short-description"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                (
                    "---\nname: short-description\n"
                    "description: Use when creating concise notes.\n"
                    "---\n\n# Notes\n\nCreate concise notes.\n"
                ),
                encoding="utf-8",
            )

            standard = lint_skill(skill_dir, policy=load_lint_policy("standard"))
            strict = lint_skill(skill_dir, policy=load_lint_policy("strict"))

            self.assertTrue(standard.passed)
            self.assertFalse(strict.passed)
            self.assertEqual(strict.error_count, 1)

    def test_custom_policy_extends_a_builtin_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "team-policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "name": "team",
                        "extends": "permissive",
                        "max_lines": 700,
                        "warnings_as_errors": ["frontmatter.extra_keys"],
                    }
                ),
                encoding="utf-8",
            )

            policy = load_lint_policy(path=policy_path)

            self.assertEqual(policy.name, "team")
            self.assertEqual(policy.max_lines, 700)
            self.assertEqual(policy.description_min_length, 40)
            self.assertEqual(policy.warnings_as_errors, {"frontmatter.extra_keys"})

    def test_custom_policy_rejects_unknown_warning_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy_path = Path(tmp) / "invalid.json"
            policy_path.write_text(
                json.dumps({"warnings_as_errors": ["unknown.warning"]}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Unknown warning codes"):
                load_lint_policy(path=policy_path)


if __name__ == "__main__":
    unittest.main()
