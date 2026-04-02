import pytest
from unittest.mock import AsyncMock, MagicMock

from benchbro.adapters.base import Capabilities
from benchbro.benchmarks.base import BenchmarkInfo, BenchmarkResult, QuestionResult
from benchbro.db.queries import create_eval_session, create_model, create_model_config
from benchbro.runner.engine import BenchmarkRunner


def _make_question_result(idx: int) -> QuestionResult:
    return QuestionResult(
        question_index=idx,
        prompt="What is 1+1?",
        raw_output="2",
        parsed_output="2",
        correct_answer="2",
        is_correct=True,
        latency_ms=50.0,
        token_count=5,
    )


def _make_benchmark_result(name: str, score: float) -> BenchmarkResult:
    return BenchmarkResult(
        benchmark_name=name,
        score=score,
        score_breakdown={"accuracy": score},
        question_results=[_make_question_result(0)],
        total_questions=1,
        correct_count=1,
    )


async def _create_session(db) -> int:
    model_id = await create_model(db, name="test-model")
    config_id = await create_model_config(
        db,
        model_id=model_id,
        backend_type="openai",
        quant_format=None,
        prompt_format="chatml",
        context_length=4096,
        sampling_params={},
    )
    session_id = await create_eval_session(db, model_config_id=config_id)
    return session_id


def _make_adapter(supports_logprobs: bool = False, supports_chat: bool = True):
    adapter = MagicMock()
    adapter.generate = AsyncMock(return_value="mock output")
    caps = Capabilities(
        supports_logprobs=supports_logprobs,
        supports_chat=supports_chat,
    )
    adapter.get_capabilities = MagicMock(return_value=caps)
    return adapter


def _make_benchmark(name: str, required_capabilities: list, score: float = 85.0):
    benchmark = MagicMock()
    info = BenchmarkInfo(
        name=name,
        category="test",
        description="A test benchmark",
        scoring_mode="accuracy",
        estimated_runtime_minutes=1,
        dataset_size=1,
        stability="stable",
        quant_sensitive=False,
        required_capabilities=required_capabilities,
    )
    benchmark.get_info = MagicMock(return_value=info)
    benchmark.get_dataset_size = MagicMock(return_value=1)
    result = _make_benchmark_result(name, score)
    benchmark.run = AsyncMock(return_value=result)
    return benchmark


@pytest.mark.asyncio
async def test_runner_executes_benchmarks(db):
    session_id = await _create_session(db)

    adapter = _make_adapter(supports_logprobs=False, supports_chat=True)
    benchmark = _make_benchmark("test_bench", required_capabilities=[], score=85.0)

    events = []
    runner = BenchmarkRunner(db, adapter, progress_callback=lambda e: events.append(e))
    results = await runner.run_session(session_id, [benchmark])

    assert len(results) == 1
    assert results[0].score == 85.0
    benchmark.run.assert_called_once()

    event_types = [e["type"] for e in events]
    assert "started" in event_types
    assert "completed" in event_types


@pytest.mark.asyncio
async def test_runner_checks_capabilities(db):
    session_id = await _create_session(db)

    # Adapter does NOT support logprobs
    adapter = _make_adapter(supports_logprobs=False, supports_chat=True)
    # Benchmark REQUIRES logprobs
    benchmark = _make_benchmark("logprobs_bench", required_capabilities=["supports_logprobs"])

    events = []
    runner = BenchmarkRunner(db, adapter, progress_callback=lambda e: events.append(e))
    results = await runner.run_session(session_id, [benchmark])

    assert results == []

    event_types = [e["type"] for e in events]
    assert "skipped" in event_types
    assert "started" not in event_types
