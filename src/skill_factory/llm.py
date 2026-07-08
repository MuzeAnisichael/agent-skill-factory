from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable
from urllib import error, request

JsonDict = dict[str, Any]
Transport = Callable[[str, JsonDict, dict[str, str], float], JsonDict]


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str


class LLMError(RuntimeError):
    """Raised when a configured LLM provider cannot complete a request."""


def create_llm_client(
    provider: str,
    model: str | None = None,
    api_base: str | None = None,
    api_key: str | None = None,
    timeout: float = 60.0,
) -> "BaseLLMClient":
    normalized = provider.strip().lower()
    if normalized == "ollama":
        return OllamaClient(
            model=model or os.getenv("OLLAMA_MODEL") or "llama3.1",
            base_url=api_base or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434",
            timeout=timeout,
        )
    if normalized in {"openai", "openai-compatible", "api"}:
        selected_model = model or os.getenv("OPENAI_MODEL")
        if not selected_model:
            raise LLMError("OpenAI-compatible provider requires --model or OPENAI_MODEL.")
        return OpenAICompatibleClient(
            model=selected_model,
            base_url=api_base or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            api_key=api_key if api_key is not None else os.getenv("OPENAI_API_KEY"),
            timeout=timeout,
        )
    raise LLMError(f"Unknown LLM provider: {provider}")


class BaseLLMClient:
    provider: str
    model: str

    def generate(self, prompt: str, system: str | None = None) -> LLMResponse:
        raise NotImplementedError


class OllamaClient(BaseLLMClient):
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        transport: Transport | None = None,
    ) -> None:
        self.provider = "ollama"
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._transport = transport or _post_json

    def generate(self, prompt: str, system: str | None = None) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: JsonDict = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        data = self._transport(f"{self.base_url}/api/chat", payload, {}, self.timeout)
        text = _extract_ollama_text(data)
        return LLMResponse(text=text, provider=self.provider, model=self.model)


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(
        self,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        api_key: str | None = None,
        timeout: float = 60.0,
        transport: Transport | None = None,
    ) -> None:
        self.provider = "openai-compatible"
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._transport = transport or _post_json

    def generate(self, prompt: str, system: str | None = None) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload: JsonDict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        data = self._transport(f"{self.base_url}/chat/completions", payload, headers, self.timeout)
        text = _extract_openai_text(data)
        return LLMResponse(text=text, provider=self.provider, model=self.model)


def _post_json(url: str, payload: JsonDict, headers: dict[str, str], timeout: float) -> JsonDict:
    body = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json", **headers}
    req = request.Request(url, data=body, headers=request_headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise LLMError(f"LLM request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise LLMError("LLM request timed out.") from exc

    try:
        data = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM provider returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise LLMError("LLM provider returned a non-object JSON response.")
    return data


def _extract_ollama_text(data: JsonDict) -> str:
    message = data.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    if isinstance(data.get("response"), str):
        return data["response"]
    raise LLMError("Ollama response did not include message.content or response.")


def _extract_openai_text(data: JsonDict) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMError("OpenAI-compatible response did not include choices.")
    first = choices[0]
    if not isinstance(first, dict):
        raise LLMError("OpenAI-compatible response choice is invalid.")
    message = first.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    if isinstance(first.get("text"), str):
        return first["text"]
    raise LLMError("OpenAI-compatible response did not include message.content.")
