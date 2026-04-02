import httpx

from .base import Capabilities, ModelAdapter, ModelMeta


class OpenAICompatAdapter(ModelAdapter):
    def __init__(self, base_url: str, model_name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def generate(self, prompt: str, params: dict) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            **params,
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions", json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def batch_generate(self, prompts: list[str], params: dict) -> list[str]:
        results = []
        for prompt in prompts:
            result = await self.generate(prompt, params)
            results.append(result)
        return results

    def get_model_metadata(self) -> ModelMeta:
        return ModelMeta(
            name=self.model_name,
            backend="openai_compat",
        )

    def get_capabilities(self) -> Capabilities:
        return Capabilities(
            supports_logprobs=True,
            supports_chat=True,
            backend_type="openai_compat",
        )

    async def logprobs(self, prompt: str, params: dict) -> list[dict]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "logprobs": True,
            "echo": True,
            **params,
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/completions", json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0].get("logprobs", {}).get("token_logprobs", [])
