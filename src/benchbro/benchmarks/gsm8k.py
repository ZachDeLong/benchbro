import re
from typing import Callable, Optional

from benchbro.benchmarks.base import (
    Benchmark,
    BenchmarkInfo,
    BenchmarkResult,
    QuestionResult,
    registry,
)

_DATASET_SIZE = 1319


class GSM8KBenchmark(Benchmark):
    def get_info(self) -> BenchmarkInfo:
        return BenchmarkInfo(
            name="gsm8k",
            category="Math",
            description=(
                "Grade-school math word problems. Tests multi-step arithmetic reasoning. "
                "Expects step-by-step solution ending with #### <answer>."
            ),
            scoring_mode="exact_match",
            estimated_runtime_minutes=20,
            dataset_size=_DATASET_SIZE,
            stability="high",
            quant_sensitive=True,
            required_capabilities=[],
        )

    def get_dataset_size(self) -> int:
        return _DATASET_SIZE

    def _load_dataset(self):
        from datasets import load_dataset

        return load_dataset("gsm8k", "main", split="test")

    def _extract_answer(self, text: str) -> str:
        """Extract numerical answer from model output.

        First looks for #### X pattern, then falls back to last number in text.
        Strips commas from numbers.
        """
        # Primary: #### pattern
        match = re.search(r"####\s*([\d,\-\.]+)", text)
        if match:
            return match.group(1).replace(",", "")

        # Fallback: last number in text
        numbers = re.findall(r"[\-]?\d[\d,]*(?:\.\d+)?", text)
        if numbers:
            return numbers[-1].replace(",", "")

        return ""

    def _extract_gold_answer(self, answer_field: str) -> str:
        """Extract gold answer from dataset answer field."""
        match = re.search(r"####\s*([\d,\-\.]+)", answer_field)
        if match:
            return match.group(1).replace(",", "")
        return answer_field.strip().replace(",", "")

    async def run(
        self,
        adapter,
        subset_mode: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BenchmarkResult:
        dataset = self._load_dataset()
        indices = self.get_subset_indices(len(dataset), subset_mode)
        total = len(indices)

        question_results: list[QuestionResult] = []
        correct_count = 0

        for run_idx, dataset_idx in enumerate(indices):
            row = dataset[dataset_idx]
            question = row["question"]
            gold_raw = row["answer"]
            gold_answer = self._extract_gold_answer(gold_raw)

            prompt = (
                "Solve this math problem step by step. "
                "End your answer with #### followed by the numerical answer.\n\n"
                f"Question: {question}\n\nAnswer:"
            )

            try:
                raw_output = await adapter.generate(prompt, {"temperature": 0.0})
            except Exception as exc:
                raw_output = str(exc)

            parsed_output = self._extract_answer(raw_output)
            is_correct = parsed_output == gold_answer
            if is_correct:
                correct_count += 1

            question_results.append(
                QuestionResult(
                    question_index=dataset_idx,
                    prompt=prompt,
                    raw_output=raw_output,
                    parsed_output=parsed_output,
                    correct_answer=gold_answer,
                    is_correct=is_correct,
                )
            )

            if progress_callback is not None:
                progress_callback(run_idx + 1, total)

        score = correct_count / total if total > 0 else 0.0

        return BenchmarkResult(
            benchmark_name="gsm8k",
            score=score,
            score_breakdown={
                "accuracy": score,
                "correct": correct_count,
                "total": total,
            },
            question_results=question_results,
            total_questions=total,
            correct_count=correct_count,
        )


# Register with the global registry
registry.register("gsm8k", GSM8KBenchmark().get_info(), GSM8KBenchmark)
