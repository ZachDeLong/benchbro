import time
from datetime import datetime, timezone
from typing import Callable, Optional

import benchbro
from benchbro.benchmarks.base import Benchmark, BenchmarkResult
from benchbro.db.queries import (
    create_run,
    create_run_detail,
    update_eval_session,
    update_run,
)


class BenchmarkRunner:
    def __init__(self, db, adapter, progress_callback: Optional[Callable] = None):
        self.db = db
        self.adapter = adapter
        self.progress_callback = progress_callback

    def _emit(self, event: dict) -> None:
        if self.progress_callback is not None:
            self.progress_callback(event)

    def _check_capabilities(self, benchmark: Benchmark) -> tuple[bool, str]:
        """Return (supported, reason). reason is empty string when supported."""
        info = benchmark.get_info()
        required = info.required_capabilities
        caps = self.adapter.get_capabilities()
        for cap in required:
            if not getattr(caps, cap, False):
                return False, f"Adapter does not support required capability: {cap}"
        return True, ""

    async def run_session(
        self,
        session_id: int,
        benchmarks: list[Benchmark],
        subset_mode: str = "full",
    ) -> list[BenchmarkResult]:
        results: list[BenchmarkResult] = []
        any_failed = False
        any_skipped = False

        for benchmark in benchmarks:
            info = benchmark.get_info()
            name = info.name

            # 1. Check capabilities
            supported, reason = self._check_capabilities(benchmark)
            if not supported:
                any_skipped = True
                self._emit({"type": "skipped", "benchmark": name, "reason": reason})
                continue

            # 2. Create run row with status "queued"
            run_id = await create_run(
                self.db,
                eval_session_id=session_id,
                benchmark_name=name,
                benchmark_version=getattr(info, "version", "unknown"),
                subset_mode=subset_mode,
                scoring_mode=info.scoring_mode,
            )

            # 3. Update status to "running", record started_at
            started_at = datetime.now(timezone.utc).isoformat()
            await update_run(
                self.db,
                run_id,
                status="running",
                started_at=started_at,
            )

            # 4. Emit "started" progress event
            self._emit({"type": "started", "benchmark": name, "run_id": run_id})

            # 5. Run the benchmark with per-question progress callback
            start_time = time.monotonic()
            try:
                total_questions = benchmark.get_dataset_size()

                def make_progress_cb(bname, rid, total):
                    def progress_cb(current: int, total_: int) -> None:
                        self._emit(
                            {
                                "type": "progress",
                                "benchmark": bname,
                                "run_id": rid,
                                "current": current,
                                "total": total_,
                            }
                        )
                    return progress_cb

                result: BenchmarkResult = await benchmark.run(
                    self.adapter,
                    subset_mode=subset_mode,
                    progress_callback=make_progress_cb(name, run_id, total_questions),
                )

                runtime_seconds = time.monotonic() - start_time
                completed_at = datetime.now(timezone.utc).isoformat()

                # 6. On success: update run
                await update_run(
                    self.db,
                    run_id,
                    status="completed",
                    score=result.score,
                    score_breakdown=result.score_breakdown,
                    runtime_seconds=runtime_seconds,
                    app_version=benchbro.__version__,
                    completed_at=completed_at,
                )

                # Store per-question details
                for qr in result.question_results:
                    await create_run_detail(
                        self.db,
                        run_id=run_id,
                        question_index=qr.question_index,
                        prompt=qr.prompt,
                        raw_output=qr.raw_output,
                        parsed_output=qr.parsed_output,
                        correct_answer=qr.correct_answer,
                        is_correct=qr.is_correct,
                        latency_ms=qr.latency_ms,
                        token_count=qr.token_count,
                    )

                self._emit(
                    {
                        "type": "completed",
                        "benchmark": name,
                        "run_id": run_id,
                        "score": result.score,
                    }
                )
                results.append(result)

            except Exception as exc:
                any_failed = True
                error_info = str(exc)
                await update_run(
                    self.db,
                    run_id,
                    status="failed",
                    error_info=error_info,
                )
                self._emit(
                    {
                        "type": "failed",
                        "benchmark": name,
                        "run_id": run_id,
                        "error": error_info,
                    }
                )

        # 8. Update eval_session status
        if any_failed or any_skipped:
            final_status = "partial"
        else:
            final_status = "completed"

        await update_eval_session(
            self.db,
            session_id,
            status=final_status,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

        return results
