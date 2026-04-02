import aiosqlite
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    param_count INTEGER,
    source TEXT,
    file_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL REFERENCES models(id),
    backend_type TEXT NOT NULL,
    quant_format TEXT,
    prompt_format TEXT NOT NULL,
    context_length INTEGER,
    sampling_params TEXT NOT NULL DEFAULT '{}',
    capabilities TEXT NOT NULL DEFAULT '{}',
    endpoint_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eval_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_config_id INTEGER NOT NULL REFERENCES model_configs(id),
    preset_used TEXT,
    subset_default TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    tags TEXT NOT NULL DEFAULT '[]',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eval_session_id INTEGER NOT NULL REFERENCES eval_sessions(id),
    benchmark_name TEXT NOT NULL,
    benchmark_version TEXT NOT NULL,
    subset_size INTEGER,
    subset_mode TEXT,
    scoring_mode TEXT,
    score REAL,
    score_breakdown TEXT DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'queued',
    error_info TEXT,
    runtime_seconds REAL,
    tokens_per_second REAL,
    hardware_info TEXT DEFAULT '{}',
    app_version TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS run_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    question_index INTEGER NOT NULL,
    prompt TEXT,
    raw_output TEXT,
    parsed_output TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    latency_ms REAL,
    token_count INTEGER
);

CREATE TABLE IF NOT EXISTS reference_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    benchmark_name TEXT NOT NULL,
    benchmark_version TEXT,
    score REAL NOT NULL,
    source TEXT,
    date_published TEXT,
    notes TEXT
);
"""


async def init_db(db_path: Path) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.executescript(SCHEMA)
    await conn.commit()
    return conn
