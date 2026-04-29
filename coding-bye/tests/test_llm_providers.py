import json
import unittest
from unittest.mock import MagicMock, patch

from agent.llm.local_provider import LocalProvider
from agent.llm.openai_provider import OpenAIProvider


class LLMProviderTests(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_openai_provider_generate(self, mocked_urlopen: MagicMock) -> None:
        payload = {"choices": [{"message": {"content": "{\"ok\":true}"}}]}
        mocked_response = MagicMock()
        mocked_response.read.return_value = json.dumps(payload).encode("utf-8")
        mocked_urlopen.return_value.__enter__.return_value = mocked_response
        provider = OpenAIProvider(base_url="https://api.openai.com/v1", model="gpt-test", api_key="k")
        result = provider.generate("hello", temperature=0.0, max_tokens=10)
        self.assertIn("ok", result.text)

    @patch("urllib.request.urlopen")
    def test_local_provider_generate(self, mocked_urlopen: MagicMock) -> None:
        payload = {"response": "{\"tool\":\"memory_tool\",\"args\":{}}"}
        mocked_response = MagicMock()
        mocked_response.read.return_value = json.dumps(payload).encode("utf-8")
        mocked_urlopen.return_value.__enter__.return_value = mocked_response
        provider = LocalProvider(base_url="http://localhost:11434", model="llama")
        result = provider.generate("hello", temperature=0.0, max_tokens=10)
        self.assertIn("memory_tool", result.text)


if __name__ == "__main__":
    unittest.main()
