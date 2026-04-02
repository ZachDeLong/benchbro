from dataclasses import dataclass, field

import httpx


@dataclass
class DetectedBackend:
    name: str
    url: str
    status: str  # "ready" | "partial" | "unreachable"
    models: list[str] = field(default_factory=list)


_KNOWN_BACKENDS = [
    {"name": "ollama", "url": "http://localhost:11434", "tags_path": "/api/tags"},
    {"name": "llama.cpp", "url": "http://localhost:8080", "tags_path": "/v1/models"},
]


async def detect_backends() -> list[DetectedBackend]:
    detected: list[DetectedBackend] = []

    for backend in _KNOWN_BACKENDS:
        name = backend["name"]
        url = backend["url"]
        tags_path = backend["tags_path"]

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{url}{tags_path}")
                response.raise_for_status()
                data = response.json()

                # Parse model list depending on backend format
                if name == "ollama":
                    models = [m["name"] for m in data.get("models", [])]
                else:
                    # OpenAI-compatible /v1/models format
                    models = [m["id"] for m in data.get("data", [])]

                status = "ready" if models else "partial"
                detected.append(
                    DetectedBackend(name=name, url=url, status=status, models=models)
                )
        except Exception:
            pass  # Swallow all errors — backend is simply unreachable

    return detected
