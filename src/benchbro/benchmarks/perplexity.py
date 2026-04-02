import math
from typing import Callable, Optional

from benchbro.benchmarks.base import (
    Benchmark,
    BenchmarkInfo,
    BenchmarkResult,
    QuestionResult,
    registry,
)

_DATASET_SIZE = 245


class PerplexityBenchmark(Benchmark):
    def get_info(self) -> BenchmarkInfo:
        return BenchmarkInfo(
            name="perplexity",
            category="Quant Quality",
            description=(
                "Measures perplexity on WikiText-2 test set. "
                "Lower is better. Uses adapter logprobs directly."
            ),
            scoring_mode="perplexity",
            estimated_runtime_minutes=10,
            dataset_size=_DATASET_SIZE,
            stability="high",
            quant_sensitive=True,
            required_capabilities=["supports_logprobs"],
        )

    def get_dataset_size(self) -> int:
        return _DATASET_SIZE

    def _load_dataset(self) -> list[str]:
        from datasets import load_dataset

        ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
        texts = [row["text"] for row in ds if row["text"].strip()]
        return texts

    async def run(
        self,
        adapter,
        subset_mode: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BenchmarkResult:
        texts = self._load_dataset()
        indices = self.get_subset_indices(len(texts), subset_mode)
        subset = [texts[i] for i in indices]
        total = len(subset)

        total_log_prob = 0.0
        total_tokens = 0
        question_results: list[QuestionResult] = []
        errors = 0

        for idx, text in enumerate(subset):
            try:
                token_logprobs: list[dict] = await adapter.logprobs(
                    text, {"temperature": 0.0}
                )
                # Each dict expected to have at minimum a "logprob" key.
                log_probs = [entry["logprob"] for entry in token_logprobs]
                n = len(log_probs)
                text_log_prob = sum(log_probs)

                total_log_prob += text_log_prob
                total_tokens += n

                qr = QuestionResult(
                    question_index=indices[idx],
                    prompt=text,
                    raw_output=str(log_probs),
                    parsed_output=str(text_log_prob),
                    correct_answer="",
                    is_correct=True,
                    token_count=n,
                )
            except Exception as exc:
                errors += 1
                qr = QuestionResult(
                    question_index=indices[idx],
                    prompt=text,
                    raw_output=str(exc),
                    parsed_output="",
                    correct_answer="",
                    is_correct=False,
                )

            question_results.append(qr)

            if progress_callback is not None:
                progress_callback(idx + 1, total)

        # Perplexity = exp(-1/N * sum(log_probs))
        if total_tokens > 0:
            perplexity = math.exp(-total_log_prob / total_tokens)
        else:
            perplexity = float("inf")

        return BenchmarkResult(
            benchmark_name="perplexity",
            score=perplexity,
            score_breakdown={
                "perplexity": perplexity,
                "total_tokens": total_tokens,
                "total_texts": total,
                "errors": errors,
            },
            question_results=question_results,
            total_questions=total,
            correct_count=total - errors,
        )


# Register with the global registry
registry.register("perplexity", PerplexityBenchmark().get_info(), PerplexityBenchmark)
