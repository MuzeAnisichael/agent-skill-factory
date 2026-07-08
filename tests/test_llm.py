import unittest

from skill_factory.llm import LLMError, OllamaClient, OpenAICompatibleClient


class LLMClientTests(unittest.TestCase):
    def test_ollama_client_uses_chat_endpoint(self) -> None:
        captured = {}

        def fake_transport(url, payload, headers, timeout):
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            captured["timeout"] = timeout
            return {"message": {"role": "assistant", "content": "{\"name\":\"demo\"}"}}

        client = OllamaClient(model="llama3.1", transport=fake_transport)
        response = client.generate("hello", system="system")

        self.assertTrue(captured["url"].endswith("/api/chat"))
        self.assertEqual(captured["payload"]["model"], "llama3.1")
        self.assertEqual(captured["payload"]["messages"][0]["role"], "system")
        self.assertEqual(response.text, "{\"name\":\"demo\"}")

    def test_openai_compatible_client_uses_chat_completions(self) -> None:
        captured = {}

        def fake_transport(url, payload, headers, timeout):
            captured["url"] = url
            captured["payload"] = payload
            captured["headers"] = headers
            return {"choices": [{"message": {"content": "{\"name\":\"demo\"}"}}]}

        client = OpenAICompatibleClient(
            model="gpt-test",
            base_url="https://example.test/v1",
            api_key="test-key",
            transport=fake_transport,
        )
        response = client.generate("hello")

        self.assertEqual(captured["url"], "https://example.test/v1/chat/completions")
        self.assertEqual(captured["payload"]["model"], "gpt-test")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(response.text, "{\"name\":\"demo\"}")

    def test_openai_compatible_requires_content(self) -> None:
        def fake_transport(url, payload, headers, timeout):
            return {"choices": [{}]}

        client = OpenAICompatibleClient(model="gpt-test", transport=fake_transport)

        with self.assertRaises(LLMError):
            client.generate("hello")


if __name__ == "__main__":
    unittest.main()
