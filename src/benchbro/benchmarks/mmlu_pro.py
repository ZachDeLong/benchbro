import re
from typing import Callable, Optional

from benchbro.benchmarks.base import (
    Benchmark,
    BenchmarkInfo,
    BenchmarkResult,
    QuestionResult,
    registry,
)

_DATASET_SIZE = 12032
CHOICES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


class MMLUProBenchmark(Benchmark):
    def get_info(self) -> BenchmarkInfo:
        return BenchmarkInfo(
            name="mmlu_pro",
            category="Knowledge",
            description=(
                "Broad knowledge benchmark with 10-choice multiple-choice questions "
                "across diverse academic disciplines."
            ),
            scoring_mode="multiple_choice",
            estimated_runtime_minutes=45,
            dataset_size=_DATASET_SIZE,
            stability="high",
            quant_sensitive=False,
            required_capabilities=[],
        )

    def get_dataset_size(self) -> int:
        return _DATASET_SIZE

    def _load_dataset(self):
        from datasets import load_dataset

        return load_dataset("TIGER-Lab/MMLU-Pro", split="test")

    def _format_choices(self, options: list[str]) -> str:
        """Format a list of option strings into lettered choice lines."""
        lines = []
        for i, opt in enumerate(options):
            letter = CHOICES[i] if i < len(CHOICES) else str(i)
            lines.append(f"{letter}. {opt}")
        return "\n".join(lines)

    def _extract_answer(self, text: str) -> str:
        """Extract single letter answer (A-J) from model output."""
        text = text.strip()

        # Single letter response (optionally followed by punctuation/whitespace)
        if re.match(r"^[A-Ja-j][.\s]*$", text):
            return text[0].upper()

        # "answer is X" pattern
        match = re.search(r"answer\s+is\s+([A-Ja-j])\b", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # First A-J letter at word boundary
        match = re.search(r"\b([A-Ja-j])\b", text)
        if match:
            return match.group(1).upper()

        return ""

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
        category_scores: dict[str, dict] = {}

        for run_idx, dataset_idx in enumerate(indices):
            row = dataset[dataset_idx]
            question = row["question"]
            options = row["options"]
            # Gold answer is stored as a letter in the "answer" field
            gold_answer = str(row["answer"]).strip().upper()
            category = str(row.get("category", "unknown"))

            formatted_choices = self._format_choices(options)
            prompt = (
                "The following is a multiple choice question. "
                "Answer with the letter of the correct option only.\n\n"
                f"Question: {question}\n\n"
                f"{formatted_choices}\n\n"
                "Answer:"
            )

            try:
                raw_output = await adapter.generate(prompt, {"temperature": 0.0})
            except Exception as exc:
                raw_output = str(exc)

            parsed_output = self._extract_answer(raw_output)
            is_correct = parsed_output == gold_answer
            if is_correct:
                correct_count += 1

            # Track per-category scores
            if category not in category_scores:
                category_scores[category] = {"correct": 0, "total": 0}
            category_scores[category]["total"] += 1
            if is_correct:
                category_scores[category]["correct"] += 1

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

        # Compute per-category accuracy
        by_category = {
            cat: v["correct"] / v["total"] if v["total"] > 0 else 0.0
            for cat, v in category_scores.items()
        }

        score = correct_count / total if total > 0 else 0.0

        return BenchmarkResult(
            benchmark_name="mmlu_pro",
            score=score,
            score_breakdown={
                "accuracy": score,
                "correct": correct_count,
                "total": total,
                "by_category": by_category,
            },
            question_results=question_results,
            total_questions=total,
            correct_count=correct_count,
        )


# Register with the global registry
registry.register("mmlu_pro", MMLUProBenchmark().get_info(), MMLUProBenchmark)
