from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class BenchmarkInfo:
    name: str
    category: str
    description: str
    scoring_mode: str
    estimated_runtime_minutes: int
    dataset_size: int
    stability: str
    quant_sensitive: bool
    required_capabilities: list[str] = field(default_factory=list)


@dataclass
class QuestionResult:
    question_index: int
    prompt: str
    raw_output: str
    parsed_output: str
    correct_answer: str
    is_correct: bool
    latency_ms: Optional[float] = None
    token_count: Optional[int] = None


@dataclass
class BenchmarkResult:
    benchmark_name: str
    score: float
    score_breakdown: dict
    question_results: list[QuestionResult]
    total_questions: int
    correct_count: int


class Benchmark(ABC):
    @abstractmethod
    def get_info(self) -> BenchmarkInfo: ...

    @abstractmethod
    def get_dataset_size(self) -> int: ...

    @abstractmethod
    async def run(
        self,
        adapter,
        subset_mode: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BenchmarkResult: ...

    def get_subset_indices(self, total: int, subset_mode: Optional[str]) -> list[int]:
        """Return indices to use for a run.

        subset_mode values:
        - None or "full": all indices
        - "25%" / "10%": that percentage of total (at least 1)
        - a digit string like "50": exact count (capped at total)
        """
        if subset_mode is None or subset_mode == "full":
            return list(range(total))

        if subset_mode.endswith("%"):
            pct = float(subset_mode.rstrip("%")) / 100.0
            count = max(1, int(total * pct))
            return list(range(count))

        if subset_mode.isdigit():
            count = min(int(subset_mode), total)
            return list(range(count))

        # Fallback: all indices
        return list(range(total))


class BenchmarkRegistry:
    def __init__(self):
        self._benchmarks: dict[str, tuple[BenchmarkInfo, type]] = {}

    def register(self, name: str, info: BenchmarkInfo, factory) -> None:
        self._benchmarks[name] = (info, factory)

    def list_benchmarks(self) -> list[str]:
        return list(self._benchmarks.keys())

    def get_info(self, name: str) -> BenchmarkInfo:
        return self._benchmarks[name][0]

    def create(self, name: str) -> Benchmark:
        return self._benchmarks[name][1]()

    def list_all_info(self) -> list[BenchmarkInfo]:
        return [info for info, _ in self._benchmarks.values()]


registry = BenchmarkRegistry()
