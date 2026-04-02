import httpx

from .base import Capabilities, ModelAdapter, ModelMeta


class OllamaAdapter(ModelAdapter):
    def __init__(self, base_url: str, model_name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def generate(self, prompt: str, params: dict) -> str:
        payload = {"model": self.model_name, "prompt": prompt, "stream": False, **params}
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def batch_generate(self, prompts: list[str], params: dict) -> list[str]:
        results = []
        for prompt in prompts:
            result = await self.generate(prompt, params)
            results.append(result)
        return results

    def get_model_metadata(self) -> ModelMeta:
        return ModelMeta(
            name=self.model_name,
            backend="ollama",
        )

    def get_capabilities(self) -> Capabilities:
        return Capabilities(
            supports_chat=True,
            backend_type="ollama",
        )

    async def fetch_model_info(self) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/show",
                json={"name": self.model_name},
            )
            response.raise_for_status()
            return response.json()

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
