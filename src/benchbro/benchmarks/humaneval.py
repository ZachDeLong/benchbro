import re
import subprocess
import tempfile
import os
from typing import Callable, Optional

from benchbro.benchmarks.base import (
    Benchmark,
    BenchmarkInfo,
    BenchmarkResult,
    QuestionResult,
    registry,
)

_DATASET_SIZE = 164


class HumanEvalBenchmark(Benchmark):
    def get_info(self) -> BenchmarkInfo:
        return BenchmarkInfo(
            name="humaneval",
            category="Coding",
            description=(
                "Python code generation benchmark. Models complete function bodies "
                "and are evaluated by running provided unit tests."
            ),
            scoring_mode="execution",
            estimated_runtime_minutes=15,
            dataset_size=_DATASET_SIZE,
            stability="medium",
            quant_sensitive=True,
            required_capabilities=[],
        )

    def get_dataset_size(self) -> int:
        return _DATASET_SIZE

    def _load_dataset(self):
        from datasets import load_dataset

        return load_dataset("openai/openai_humaneval", split="test")

    def _extract_code(self, text: str) -> str:
        """Extract code from model output.

        Checks for ```python blocks, then ``` blocks, else returns raw output.
        """
        # Try ```python ... ``` block
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try ``` ... ``` block (any language tag)
        match = re.search(r"```(?:\w+)?\s*(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fall back to raw output
        return text.strip()

    def _run_tests(self, prompt_code: str, completion: str, test_code: str) -> bool:
        """Write full code to a temp file and run with subprocess (timeout=10s).

        Returns True if the process exits with returncode 0.
        """
        full_code = prompt_code + "\n" + completion + "\n\n" + test_code + "\n\ncheck(candidate)"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(full_code)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["python", tmp_path],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

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
            prompt_code = row["prompt"]
            test_code = row["test"]
            # "entry_point" is the function name the test calls as candidate
            entry_point = row.get("entry_point", "")

            prompt = (
                "Complete the following Python function. "
                "Only output the function body, no explanation.\n\n"
                f"{prompt_code}"
            )

            try:
                raw_output = await adapter.complete(prompt, {"temperature": 0.0})
            except Exception as exc:
                raw_output = str(exc)

            completion = self._extract_code(raw_output)

            # Build the test harness: alias entry_point as candidate
            test_harness = test_code + f"\n\ncandidate = {entry_point}"
            is_correct = self._run_tests(prompt_code, completion, test_harness)
            if is_correct:
                correct_count += 1

            question_results.append(
                QuestionResult(
                    question_index=dataset_idx,
                    prompt=prompt,
                    raw_output=raw_output,
                    parsed_output=completion,
                    correct_answer=entry_point,
                    is_correct=is_correct,
                )
            )

            if progress_callback is not None:
                progress_callback(run_idx + 1, total)

        score = correct_count / total if total > 0 else 0.0

        return BenchmarkResult(
            benchmark_name="humaneval",
            score=score,
            score_breakdown={
                "pass@1": score,
                "correct": correct_count,
                "total": total,
            },
            question_results=question_results,
            total_questions=total,
            correct_count=correct_count,
        )


# Register with the global registry
registry.register("humaneval", HumanEvalBenchmark().get_info(), HumanEvalBenchmark)
