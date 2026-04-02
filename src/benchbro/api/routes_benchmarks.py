from dataclasses import asdict

from fastapi import APIRouter

from benchbro.benchmarks.base import registry

router = APIRouter()

PRESETS = {
    "quick": {
        "name": "Quick Check",
        "description": "Fast sanity check (~10 min)",
        "benchmarks": {"gsm8k": "10%", "perplexity": "full"},
    },
    "full": {
        "name": "Full Eval",
        "description": "All benchmarks, full datasets (~2.5 hrs)",
        "benchmarks": {
            "mmlu_pro": "full",
            "gsm8k": "full",
            "humaneval": "full",
            "perplexity": "full",
        },
    },
    "coding": {
        "name": "Coding",
        "description": "Code generation focus (~15 min)",
        "benchmarks": {"humaneval": "full"},
    },
    "quant": {
        "name": "Quant Comparison",
        "description": "Optimized for detecting quantization damage (~45 min)",
        "benchmarks": {"perplexity": "full", "gsm8k": "full", "mmlu_pro": "25%"},
    },
}


@router.get("/benchmarks")
async def list_benchmarks():
    infos = registry.list_all_info()
    return [asdict(info) for info in infos]


@router.get("/benchmarks/presets")
async def list_presets():
    return PRESETS
