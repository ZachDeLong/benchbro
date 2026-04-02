from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from benchbro.config import Config
from benchbro.db.schema import init_db


def create_app(db_path: Path | None = None) -> FastAPI:
    config = Config()
    if db_path is not None:
        config.db_path = db_path

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db = await init_db(config.db_path)
        yield
        await app.state.db.close()

    app = FastAPI(title="BenchBro", version="0.1.0", lifespan=lifespan)
    app.state.config = config

    # Trigger benchmark registry registration by importing modules
    import benchbro.benchmarks.perplexity  # noqa: F401
    import benchbro.benchmarks.gsm8k  # noqa: F401
    import benchbro.benchmarks.mmlu_pro  # noqa: F401
    import benchbro.benchmarks.humaneval  # noqa: F401

    # Register API routers
    from benchbro.api.routes_models import router as models_router
    from benchbro.api.routes_benchmarks import router as benchmarks_router
    from benchbro.api.routes_sessions import router as sessions_router

    app.include_router(models_router, prefix="/api")
    app.include_router(benchmarks_router, prefix="/api")
    app.include_router(sessions_router, prefix="/api")

    # Health endpoint
    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # Serve built frontend if static dir exists
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/{path:path}")
        async def serve_spa(request: Request, path: str):
            # Serve actual files if they exist, otherwise index.html for SPA routing
            file_path = static_dir / path
            if file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(static_dir / "index.html")

    return app
