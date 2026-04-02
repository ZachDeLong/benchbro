# BenchBro

Local LLM benchmarking with a friendly web UI.

## Install

```bash
pip install benchbro
```

## Usage

```bash
# Start Ollama (or llama.cpp server) first, then:
benchbro
```

Browser opens automatically. Select your model, pick benchmarks, run, and compare results.

## Supported Backends

- **Ollama** — auto-detected at localhost:11434
- **OpenAI-compatible** — llama.cpp server, LM Studio, vLLM, TabbyAPI

## Benchmarks (v1)

| Benchmark | Category | What it tests |
|-----------|----------|---------------|
| MMLU-Pro | Knowledge | Broad knowledge across 57 subjects |
| GSM8K | Math | Grade-school math word problems |
| HumanEval | Coding | Python code generation |
| Perplexity | Quant Quality | Raw language modeling (WikiText-2) |

## Development

```bash
git clone https://github.com/zachdelong/benchbro
cd benchbro
pip install -e ".[dev]"
cd frontend && npm install && npm run build && cd ..
python -m pytest tests/ -v
benchbro
```

## License

MIT
