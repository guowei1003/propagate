import httpx
from typing import Any
from app.config import get_settings

settings = get_settings()


def _demo_response(prompt: str) -> str:
    """Generate a mock response based on the prompt content."""
    prompt_lower = prompt.lower()
    if "write" in prompt_lower or "code" in prompt_lower or "python" in prompt_lower:
        return (
            "# Generated Code\n\n"
            "def main():\n"
            "    print('Hello from Propagate!')\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
    elif "analyze" in prompt_lower or "review" in prompt_lower:
        return "Analysis complete. No issues found."
    elif "test" in prompt_lower:
        return "All tests passed successfully."
    else:
        return f"# Propagate Demo Output\n\nProcessed: {prompt[:100]}...\n\nTask completed in demo mode."


class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider
        self.api_base = settings.llm_api_base
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    def complete(self, prompt: str, **kwargs: Any) -> str:
        if self.provider == "demo":
            return _demo_response(prompt)

        if self.provider == "openai":
            return self._openai_complete(prompt, **kwargs)
        if self.provider == "ollama":
            return self._ollama_complete(prompt, **kwargs)

        return _demo_response(prompt)

    def _openai_complete(self, prompt: str, **kwargs: Any) -> str:
        try:
            with httpx.Client(timeout=kwargs.get("timeout", 60)) as client:
                resp = client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": kwargs.get("temperature", 0.2),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[LLM Error] {e}"

    def _ollama_complete(self, prompt: str, **kwargs: Any) -> str:
        try:
            with httpx.Client(timeout=kwargs.get("timeout", 60)) as client:
                resp = client.post(
                    f"{self.api_base}/api/generate",
                    json={"model": self.model, "prompt": prompt},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
        except Exception as e:
            return f"[LLM Error] {e}"


llm_service = LLMService()
