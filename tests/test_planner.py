import unittest

from skill_factory.llm import BaseLLMClient, LLMError, LLMResponse
from skill_factory.planner import parse_plan_payload, plan_skill_with_llm


class FakeClient(BaseLLMClient):
    provider = "fake"
    model = "fake-model"

    def __init__(self, text: str) -> None:
        self.text = text
        self.prompt = ""
        self.system = None

    def generate(self, prompt: str, system: str | None = None) -> LLMResponse:
        self.prompt = prompt
        self.system = system
        return LLMResponse(text=self.text, provider=self.provider, model=self.model)


class PlannerTests(unittest.TestCase):
    def test_parse_plan_payload_extracts_json_object(self) -> None:
        payload = parse_plan_payload('Here is the plan: {"name": "Demo Skill"}')

        self.assertEqual(payload["name"], "Demo Skill")

    def test_parse_plan_payload_rejects_missing_json(self) -> None:
        with self.assertRaises(LLMError):
            parse_plan_payload("not json")

    def test_plan_skill_with_llm_returns_normalized_skill_plan(self) -> None:
        client = FakeClient(
            """
            {
              "name": "Release Note Builder",
              "description": "Use this skill when the agent needs release notes from repository changes.",
              "brief": "Create release notes from merged pull requests.",
              "resources": ["references", "scripts"],
              "examples": ["Create release notes for this branch."]
            }
            """
        )

        plan = plan_skill_with_llm(client, brief="Release-note workflow source material.")

        self.assertEqual(plan.name, "release-note-builder")
        self.assertEqual(plan.resources, ("references", "scripts"))
        self.assertIn("Create release notes", plan.examples[0])
        self.assertIn("Release-note workflow source material", client.prompt)

    def test_cli_overrides_take_precedence(self) -> None:
        client = FakeClient(
            """
            {
              "name": "Bad Name",
              "description": "Bad description",
              "brief": "Generated brief",
              "resources": ["assets"],
              "examples": ["Generated example"]
            }
            """
        )

        plan = plan_skill_with_llm(
            client,
            brief="Source brief",
            name="Preferred Name",
            description="Use this skill when the preferred workflow should be applied.",
            resources=("references",),
            examples=("Preferred example",),
        )

        self.assertEqual(plan.name, "preferred-name")
        self.assertEqual(plan.resources, ("references",))
        self.assertEqual(plan.description, "Use this skill when the preferred workflow should be applied.")
        self.assertEqual(plan.examples, ("Generated example", "Preferred example"))


if __name__ == "__main__":
    unittest.main()
