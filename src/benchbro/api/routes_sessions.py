import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from benchbro.adapters.ollama import OllamaAdapter
from benchbro.adapters.openai_compat import OpenAICompatAdapter
from benchbro.benchmarks.base import registry
from benchbro.db.queries import (
    create_eval_session,
    create_model,
    create_model_config,
    get_eval_session,
    get_run_details,
    get_runs_for_session,
    list_eval_sessions,
)
from benchbro.runner.engine import BenchmarkRunner

router = APIRouter()


class StartSessionRequest(BaseModel):
    model_name: str
    backend_type: str
    backend_url: str
    quant_format: Optional[str] = None
    prompt_format: str = "chat"
    context_length: int = 4096
    sampling_params: dict = {}
    benchmarks: dict[str, str]  # benchmark_name -> subset_mode
    preset: Optional[str] = None
    tags: list[str] = []
    notes: str = ""


@router.post("/sessions/start")
async def start_session(request: Request, body: StartSessionRequest):
    db = request.app.state.db

    # Create model record
    model_id = await create_model(db, name=body.model_name)

    # Create model config record
    config_id = await create_model_config(
        db,
        model_id=model_id,
        backend_type=body.backend_type,
        quant_format=body.quant_format,
        prompt_format=body.prompt_format,
        context_length=body.context_length,
        sampling_params=body.sampling_params,
        endpoint_url=body.backend_url,
    )

    # Create eval session record
    session_id = await create_eval_session(
        db,
        model_config_id=config_id,
        preset_used=body.preset,
    )

    # Build adapter
    if body.backend_type == "ollama":
        adapter = OllamaAdapter(base_url=body.backend_url, model_name=body.model_name)
    else:
        adapter = OpenAICompatAdapter(base_url=body.backend_url, model_name=body.model_name)

    # Build benchmark instances from registry
    benchmark_instances = []
    for name in body.benchmarks:
        try:
            benchmark_instances.append(registry.create(name))
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Unknown benchmark: {name}")

    # Determine subset_mode: use "full" as default; individual overrides are
    # not yet threaded through run_session per-benchmark, so we use the first
    # subset_mode value if there is exactly one benchmark, otherwise "full".
    subset_modes = list(body.benchmarks.values())
    subset_mode = subset_modes[0] if len(subset_modes) == 1 else "full"

    runner = BenchmarkRunner(db=db, adapter=adapter)

    # Launch in background
    asyncio.create_task(
        runner.run_session(
            session_id=session_id,
            benchmarks=benchmark_instances,
            subset_mode=subset_mode,
        )
    )

    return {"session_id": session_id, "status": "started"}


@router.get("/sessions")
async def list_sessions(request: Request):
    db = request.app.state.db
    return await list_eval_sessions(db)


@router.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: int):
    db = request.app.state.db
    session = await get_eval_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    runs = await get_runs_for_session(db, session_id)
    return {"session": session, "runs": runs}


@router.get("/runs/{run_id}/details")
async def get_run_detail(request: Request, run_id: int):
    db = request.app.state.db
    details = await get_run_details(db, run_id)
    return details
