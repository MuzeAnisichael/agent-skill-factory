from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence

from .llm import BaseLLMClient, LLMError


MAX_RUNNER_OUTPUT_BYTES = 1_000_000


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


class RunnerError(RuntimeError):
    """Raised when an eval runner cannot produce a valid result."""


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

        try:
            response = self._client.generate(user_prompt, system=system)
        except LLMError as exc:
            raise RunnerError(str(exc)) from exc
        return RunnerResult(
            output=response.text,
            runner=self.name,
            used_skill=use_skill,
            metadata={
                "provider": response.provider,
                "model": response.model,
            },
        )


class SubprocessEvalRunner:
    """Run an external Agent adapter over a validated JSON stdin/stdout protocol."""

    name = "subprocess"

    def __init__(self, command: Sequence[str], timeout: float = 60.0) -> None:
        if not command or any(not isinstance(item, str) or not item for item in command):
            raise ValueError("Subprocess runner command must contain non-empty arguments.")
        if timeout <= 0:
            raise ValueError("Subprocess runner timeout must be greater than zero.")
        self.command = tuple(command)
        self.timeout = timeout

    def run(self, prompt: str, skill: SkillContext, use_skill: bool) -> RunnerResult:
        skill_payload = None
        if use_skill:
            skill_payload = {
                "name": skill.name,
                "description": skill.description,
                "body": skill.body,
                "text": skill.text,
                "path": str(skill.path),
            }
        payload = {
            "schema_version": 1,
            "prompt": prompt,
            "use_skill": use_skill,
            "skill": skill_payload,
        }
        try:
            completed = subprocess.run(
                self.command,
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=self.timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RunnerError(
                f"Subprocess runner timed out after {self.timeout:g} seconds."
            ) from exc
        except OSError as exc:
            raise RunnerError(f"Could not start subprocess runner: {exc}") from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or "no stderr output"
            raise RunnerError(
                f"Subprocess runner exited with code {completed.returncode}: {detail[:500]}"
            )
        if len(completed.stdout.encode("utf-8")) > MAX_RUNNER_OUTPUT_BYTES:
            raise RunnerError("Subprocess runner output exceeded 1000000 bytes.")
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RunnerError("Subprocess runner did not return valid JSON.") from exc
        if not isinstance(response, dict):
            raise RunnerError("Subprocess runner response must be a JSON object.")
        output = response.get("output")
        if not isinstance(output, str):
            raise RunnerError("Subprocess runner response requires a string output field.")
        raw_metadata = response.get("metadata", {})
        if not isinstance(raw_metadata, dict):
            raise RunnerError("Subprocess runner metadata must be a JSON object when present.")
        metadata = {
            str(key): value if isinstance(value, str) else json.dumps(value, sort_keys=True)
            for key, value in raw_metadata.items()
        }
        return RunnerResult(
            output=output,
            runner=self.name,
            used_skill=use_skill,
            metadata=metadata,
        )
