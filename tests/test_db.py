import pytest
from benchbro.db.queries import (
    create_eval_session,
    create_model,
    create_model_config,
    create_run,
    get_eval_session,
    list_eval_sessions,
)


EXPECTED_TABLES = {
    "models",
    "model_configs",
    "eval_sessions",
    "runs",
    "run_details",
    "reference_scores",
}


@pytest.mark.asyncio
async def test_init_db_creates_tables(db):
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    rows = await cursor.fetchall()
    actual_tables = {row["name"] for row in rows}
    assert actual_tables == EXPECTED_TABLES


@pytest.mark.asyncio
async def test_create_model_and_config(db):
    model_id = await create_model(db, name="llama-3-8b", param_count=8_000_000_000, source="hf")
    assert isinstance(model_id, int)
    assert model_id > 0

    config_id = await create_model_config(
        db,
        model_id=model_id,
        backend_type="llama_cpp",
        quant_format="Q4_K_M",
        prompt_format="chatml",
        context_length=4096,
        sampling_params={"temperature": 0.0},
    )
    assert isinstance(config_id, int)
    assert config_id > 0

    cursor = await db.execute("SELECT * FROM model_configs WHERE id = ?", (config_id,))
    row = await cursor.fetchone()
    assert row is not None
    assert row["model_id"] == model_id
    assert row["backend_type"] == "llama_cpp"
    assert row["quant_format"] == "Q4_K_M"


@pytest.mark.asyncio
async def test_create_and_get_eval_session(db):
    model_id = await create_model(db, name="mistral-7b")
    config_id = await create_model_config(
        db,
        model_id=model_id,
        backend_type="ollama",
        quant_format=None,
        prompt_format="mistral",
        context_length=8192,
        sampling_params={},
    )

    session_id = await create_eval_session(
        db,
        model_config_id=config_id,
        preset_used="quick",
        subset_default="100",
    )
    assert isinstance(session_id, int)

    session = await get_eval_session(db, session_id)
    assert session is not None
    assert session["id"] == session_id
    assert session["model_config_id"] == config_id
    assert session["preset_used"] == "quick"
    assert session["subset_default"] == "100"
    assert session["status"] == "running"


@pytest.mark.asyncio
async def test_create_run_in_session(db):
    model_id = await create_model(db, name="phi-3-mini")
    config_id = await create_model_config(
        db,
        model_id=model_id,
        backend_type="llama_cpp",
        quant_format="Q8_0",
        prompt_format="phi3",
        context_length=2048,
        sampling_params={"temperature": 0.0, "top_p": 1.0},
    )
    session_id = await create_eval_session(db, model_config_id=config_id)

    run_id = await create_run(
        db,
        eval_session_id=session_id,
        benchmark_name="gsm8k",
        benchmark_version="1.0.0",
        subset_size=50,
        subset_mode="random",
        scoring_mode="exact_match",
    )
    assert isinstance(run_id, int)
    assert run_id > 0

    cursor = await db.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    row = await cursor.fetchone()
    assert row is not None
    assert row["eval_session_id"] == session_id
    assert row["benchmark_name"] == "gsm8k"
    assert row["benchmark_version"] == "1.0.0"
    assert row["subset_size"] == 50
    assert row["status"] == "queued"


@pytest.mark.asyncio
async def test_list_eval_sessions(db):
    model_id = await create_model(db, name="gemma-2b")
    config_id = await create_model_config(
        db,
        model_id=model_id,
        backend_type="ollama",
        quant_format=None,
        prompt_format="gemma",
        context_length=4096,
        sampling_params={},
    )

    session_id_1 = await create_eval_session(db, model_config_id=config_id, preset_used="quick")
    session_id_2 = await create_eval_session(db, model_config_id=config_id, preset_used="full")

    sessions = await list_eval_sessions(db)
    assert len(sessions) == 2
    ids = {s["id"] for s in sessions}
    assert session_id_1 in ids
    assert session_id_2 in ids
