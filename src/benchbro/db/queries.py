import json
from typing import Any

import aiosqlite

# Fields allowed for update_run
_RUN_ALLOWED_FIELDS = {
    "status",
    "score",
    "score_breakdown",
    "error_info",
    "runtime_seconds",
    "tokens_per_second",
    "hardware_info",
    "app_version",
    "started_at",
    "completed_at",
}

# Fields allowed for update_eval_session
_SESSION_ALLOWED_FIELDS = {"status", "completed_at", "tags", "notes"}

# JSON fields that must be serialized before storage
_JSON_FIELDS = {"sampling_params", "score_breakdown", "hardware_info", "tags", "capabilities"}


def _serialize(key: str, value: Any) -> Any:
    """Serialize a value to JSON string if it's a JSON field."""
    if key in _JSON_FIELDS and not isinstance(value, str):
        return json.dumps(value)
    return value


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


async def create_model(
    db: aiosqlite.Connection,
    name: str,
    param_count: int | None = None,
    source: str | None = None,
    file_hash: str | None = None,
) -> int:
    cursor = await db.execute(
        "INSERT INTO models (name, param_count, source, file_hash) VALUES (?, ?, ?, ?)",
        (name, param_count, source, file_hash),
    )
    await db.commit()
    return cursor.lastrowid


async def create_model_config(
    db: aiosqlite.Connection,
    model_id: int,
    backend_type: str,
    quant_format: str | None,
    prompt_format: str,
    context_length: int | None,
    sampling_params: dict | str,
    endpoint_url: str | None = None,
) -> int:
    cursor = await db.execute(
        """INSERT INTO model_configs
           (model_id, backend_type, quant_format, prompt_format, context_length, sampling_params, endpoint_url)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            model_id,
            backend_type,
            quant_format,
            prompt_format,
            context_length,
            _serialize("sampling_params", sampling_params),
            endpoint_url,
        ),
    )
    await db.commit()
    return cursor.lastrowid


async def create_eval_session(
    db: aiosqlite.Connection,
    model_config_id: int,
    preset_used: str | None = None,
    subset_default: str | None = None,
) -> int:
    cursor = await db.execute(
        "INSERT INTO eval_sessions (model_config_id, preset_used, subset_default) VALUES (?, ?, ?)",
        (model_config_id, preset_used, subset_default),
    )
    await db.commit()
    return cursor.lastrowid


async def get_eval_session(db: aiosqlite.Connection, session_id: int) -> dict | None:
    cursor = await db.execute(
        """SELECT es.*, m.name AS model_name, mc.backend_type
           FROM eval_sessions es
           JOIN model_configs mc ON es.model_config_id = mc.id
           JOIN models m ON mc.model_id = m.id
           WHERE es.id = ?""",
        (session_id,),
    )
    row = await cursor.fetchone()
    return _row_to_dict(row) if row is not None else None


async def list_eval_sessions(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        """SELECT es.*, m.name AS model_name, mc.backend_type
           FROM eval_sessions es
           JOIN model_configs mc ON es.model_config_id = mc.id
           JOIN models m ON mc.model_id = m.id
           ORDER BY es.id DESC"""
    )
    rows = await cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


async def create_run(
    db: aiosqlite.Connection,
    eval_session_id: int,
    benchmark_name: str,
    benchmark_version: str,
    subset_size: int | None = None,
    subset_mode: str | None = None,
    scoring_mode: str | None = None,
) -> int:
    cursor = await db.execute(
        """INSERT INTO runs
           (eval_session_id, benchmark_name, benchmark_version, subset_size, subset_mode, scoring_mode)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (eval_session_id, benchmark_name, benchmark_version, subset_size, subset_mode, scoring_mode),
    )
    await db.commit()
    return cursor.lastrowid


async def update_run(db: aiosqlite.Connection, run_id: int, **kwargs) -> None:
    unknown = set(kwargs) - _RUN_ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"Unknown fields for update_run: {unknown}")
    if not kwargs:
        return
    serialized = {k: _serialize(k, v) for k, v in kwargs.items()}
    set_clause = ", ".join(f"{k} = ?" for k in serialized)
    values = list(serialized.values()) + [run_id]
    await db.execute(f"UPDATE runs SET {set_clause} WHERE id = ?", values)
    await db.commit()


async def update_eval_session(db: aiosqlite.Connection, session_id: int, **kwargs) -> None:
    unknown = set(kwargs) - _SESSION_ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"Unknown fields for update_eval_session: {unknown}")
    if not kwargs:
        return
    serialized = {k: _serialize(k, v) for k, v in kwargs.items()}
    set_clause = ", ".join(f"{k} = ?" for k in serialized)
    values = list(serialized.values()) + [session_id]
    await db.execute(f"UPDATE eval_sessions SET {set_clause} WHERE id = ?", values)
    await db.commit()


async def create_run_detail(
    db: aiosqlite.Connection,
    run_id: int,
    question_index: int,
    prompt: str | None,
    raw_output: str | None,
    parsed_output: str | None,
    correct_answer: str | None,
    is_correct: bool | None,
    latency_ms: float | None = None,
    token_count: int | None = None,
) -> int:
    cursor = await db.execute(
        """INSERT INTO run_details
           (run_id, question_index, prompt, raw_output, parsed_output, correct_answer,
            is_correct, latency_ms, token_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id,
            question_index,
            prompt,
            raw_output,
            parsed_output,
            correct_answer,
            is_correct,
            latency_ms,
            token_count,
        ),
    )
    await db.commit()
    return cursor.lastrowid


async def get_runs_for_session(db: aiosqlite.Connection, session_id: int) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM runs WHERE eval_session_id = ? ORDER BY id", (session_id,)
    )
    rows = await cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


async def get_run_details(db: aiosqlite.Connection, run_id: int) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM run_details WHERE run_id = ? ORDER BY question_index", (run_id,)
    )
    rows = await cursor.fetchall()
    return [_row_to_dict(r) for r in rows]
