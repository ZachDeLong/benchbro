from fastapi import APIRouter, Request

from benchbro.adapters.detection import detect_backends

router = APIRouter()


@router.get("/models/backends")
async def list_backends(request: Request):
    backends = await detect_backends()
    return [
        {
            "name": b.name,
            "url": b.url,
            "status": b.status,
            "models": b.models,
        }
        for b in backends
    ]
