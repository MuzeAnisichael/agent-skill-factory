import unittest
from pathlib import Path

from skill_factory.llm import LLMResponse
from skill_factory.runner import DryRunRunner, LLMEvalRunner, SkillContext


class FakeClient:
    provider = "fake"
    model = "test-model"

    def __init__(self) -> None:
        self.prompt = ""
        self.system = ""

    def generate(self, prompt: str, system: str | None = None) -> LLMResponse:
        self.prompt = prompt
        self.system = system or ""
        return LLMResponse(text="features\nfixes", provider=self.provider, model=self.model)


class RunnerTests(unittest.TestCase):
    def test_dry_run_runner_adds_skill_context_only_when_requested(self) -> None:
        skill = self.skill_context()
        runner = DryRunRunner()

        baseline = runner.run("Create release notes.", skill, use_skill=False)
        with_skill = runner.run("Create release notes.", skill, use_skill=True)

        self.assertIn("No Skill context was loaded", baseline.output)
        self.assertNotIn("Skill: release-note-builder", baseline.output)
        self.assertIn("Skill: release-note-builder", with_skill.output)
        self.assertIn("features section", with_skill.output)

    def test_llm_runner_supplies_skill_context(self) -> None:
        skill = self.skill_context()
        client = FakeClient()
        runner = LLMEvalRunner(client)

        result = runner.run("Create release notes.", skill, use_skill=True)

        self.assertEqual(result.output, "features\nfixes")
        self.assertEqual(result.metadata["provider"], "fake")
        self.assertIn("Skill context", client.prompt)
        self.assertIn("release-note-builder", client.prompt)

    def skill_context(self) -> SkillContext:
        return SkillContext(
            name="release-note-builder",
            description="Use this skill when creating release notes.",
            body="Include a features section and a fixes section.",
            text="release-note-builder Include a features section and a fixes section.",
            path=Path("release-note-builder"),
        )


if __name__ == "__main__":
    unittest.main()
