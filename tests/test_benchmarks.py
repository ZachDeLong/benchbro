import pytest

from benchbro.benchmarks.base import (
    Benchmark,
    BenchmarkInfo,
    BenchmarkRegistry,
    BenchmarkResult,
    QuestionResult,
)
from benchbro.benchmarks.perplexity import PerplexityBenchmark
from benchbro.benchmarks.gsm8k import GSM8KBenchmark
from benchbro.benchmarks.mmlu_pro import MMLUProBenchmark
from benchbro.benchmarks.humaneval import HumanEvalBenchmark


# ---------------------------------------------------------------------------
# 1. BenchmarkRegistry
# ---------------------------------------------------------------------------

def test_benchmark_registry():
    reg = BenchmarkRegistry()

    info = BenchmarkInfo(
        name="dummy",
        category="Test",
        description="A dummy benchmark",
        scoring_mode="accuracy",
        estimated_runtime_minutes=1,
        dataset_size=10,
        stability="high",
        quant_sensitive=False,
        required_capabilities=[],
    )

    class DummyBenchmark(Benchmark):
        def get_info(self) -> BenchmarkInfo:
            return info

        def get_dataset_size(self) -> int:
            return 10

        async def run(self, adapter, subset_mode=None, progress_callback=None):
            return BenchmarkResult(
                benchmark_name="dummy",
                score=1.0,
                score_breakdown={},
                question_results=[],
                total_questions=0,
                correct_count=0,
            )

    reg.register("dummy", info, DummyBenchmark)

    assert "dummy" in reg.list_benchmarks()
    retrieved_info = reg.get_info("dummy")
    assert retrieved_info.name == "dummy"
    assert retrieved_info.category == "Test"
    assert retrieved_info.scoring_mode == "accuracy"


# ---------------------------------------------------------------------------
# 2. PerplexityBenchmark info fields
# ---------------------------------------------------------------------------

def test_perplexity_benchmark_info():
    bench = PerplexityBenchmark()
    info = bench.get_info()

    assert info.name == "perplexity"
    assert info.scoring_mode == "perplexity"
    assert "supports_logprobs" in info.required_capabilities
    assert info.quant_sensitive is True
    assert info.stability == "high"
    assert info.category == "Quant Quality"


# ---------------------------------------------------------------------------
# 3. get_subset_indices with "10%"
# ---------------------------------------------------------------------------

def test_perplexity_benchmark_subset():
    bench = PerplexityBenchmark()
    total = 245
    indices = bench.get_subset_indices(total, "10%")

    expected_count = max(1, int(total * 0.10))
    assert len(indices) == expected_count
    assert indices == list(range(expected_count))


# ---------------------------------------------------------------------------
# 4. GSM8K info
# ---------------------------------------------------------------------------

def test_gsm8k_info():
    bench = GSM8KBenchmark()
    info = bench.get_info()

    assert info.name == "gsm8k"
    assert info.category == "Math"
    assert info.scoring_mode == "exact_match"


# ---------------------------------------------------------------------------
# 5. MMLU-Pro info
# ---------------------------------------------------------------------------

def test_mmlu_pro_info():
    bench = MMLUProBenchmark()
    info = bench.get_info()

    assert info.name == "mmlu_pro"
    assert info.category == "Knowledge"
    assert info.scoring_mode == "multiple_choice"


# ---------------------------------------------------------------------------
# 6. HumanEval info
# ---------------------------------------------------------------------------

def test_humaneval_info():
    bench = HumanEvalBenchmark()
    info = bench.get_info()

    assert info.name == "humaneval"
    assert info.category == "Coding"
    assert info.scoring_mode == "execution"


# ---------------------------------------------------------------------------
# 7. All four benchmarks registered in the global registry
# ---------------------------------------------------------------------------

def test_all_benchmarks_registered():
    # Importing the modules triggers module-level registry.register() calls.
    # They are already imported at the top of this file, so registry is populated.
    from benchbro.benchmarks.base import registry

    registered = registry.list_benchmarks()
    for expected in ("perplexity", "gsm8k", "mmlu_pro", "humaneval"):
        assert expected in registered, f"{expected!r} not found in registry: {registered}"
