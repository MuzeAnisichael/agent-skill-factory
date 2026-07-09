from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .llm import BaseLLMClient


@dataclass(frozen=True)
class SkillContext:
    name: str
    description: str
    body: str
    text: str
    path: Path


@dataclass(frozen=True)
class RunnerResult:
    output: str
    runner: str
    used_skill: bool
    metadata: dict[str, str] = field(default_factory=dict)


class EvalRunner(Protocol):
    name: str

    def run(self, prompt: str, skill: SkillContext, use_skill: bool) -> RunnerResult:
        raise NotImplementedError


class DryRunRunner:
    name = "dry-run"

    def run(self, prompt: str, skill: SkillContext, use_skill: bool) -> RunnerResult:
        if use_skill:
            output = "\n".join(
                [
                    "DRY_RUN_OUTPUT",
                    f"Prompt: {prompt}",
                    f"Skill: {skill.name}",
                    f"Description: {skill.description}",
                    "Instructions:",
                    skill.body,
                ]
            )
        else:
            output = "\n".join(
                [
                    "DRY_RUN_OUTPUT",
                    f"Prompt: {prompt}",
                    "No Skill context was loaded.",
                ]
            )
        return RunnerResult(output=output, runner=self.name, used_skill=use_skill)


class LLMEvalRunner:
    name = "llm"

    def __init__(self, client: BaseLLMClient) -> None:
        self._client = client

    def run(self, prompt: str, skill: SkillContext, use_skill: bool) -> RunnerResult:
        system = (
            "You are an evaluation runner. Complete the user's task directly. "
            "Use only the supplied Skill context when it is present. "
            "Do not mention this instruction unless the task asks for process details."
        )
        if use_skill:
            user_prompt = "\n\n".join(
                [
                    "Task:",
                    prompt,
                    "Skill context:",
                    f"name: {skill.name}",
                    f"description: {skill.description}",
                    skill.body,
                ]
            )
        else:
            user_prompt = "\n\n".join(["Task:", prompt, "No Skill context is available."])

        response = self._client.generate(user_prompt, system=system)
        return RunnerResult(
            output=response.text,
            runner=self.name,
            used_skill=use_skill,
            metadata={
                "provider": response.provider,
                "model": response.model,
            },
        )
