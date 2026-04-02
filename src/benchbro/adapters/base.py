from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Capabilities:
    supports_logprobs: bool = False
    supports_batching: bool = False
    supports_chat: bool = False
    supports_stop_sequences: bool = False
    supports_token_count: bool = False
    max_context_known: int | None = None
    backend_type: str = "generic"


@dataclass
class ModelMeta:
    name: str
    param_count: int | None = None
    quant_format: str | None = None
    context_length: int | None = None
    backend: str = "unknown"
    file_hash: str | None = None
    extra: dict = field(default_factory=dict)


class ModelAdapter(ABC):
    @abstractmethod
    async def generate(self, prompt: str, params: dict) -> str: ...

    @abstractmethod
    async def batch_generate(self, prompts: list[str], params: dict) -> list[str]: ...

    @abstractmethod
    def get_model_metadata(self) -> ModelMeta: ...

    @abstractmethod
    def get_capabilities(self) -> Capabilities: ...

    # Optional — override if supported
    async def logprobs(self, prompt: str, params: dict) -> list[dict]:
        raise NotImplementedError("This adapter does not support logprobs")

    async def tokenize(self, text: str) -> list[int]:
        raise NotImplementedError("This adapter does not support tokenize")
