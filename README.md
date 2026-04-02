# benchbro

benchmark your local LLMs without the headache. runs in a browser, talks to ollama or llama.cpp.

early/alpha — works but rough around the edges.

## setup

```
pip install -e .
cd frontend && npm install && npm run build && cd ..
```

## usage

```
# have ollama running with a model pulled, then:
benchbro
```

opens a browser. pick your model, pick a benchmark, run it, see results.

## benchmarks

- MMLU-Pro (knowledge)
- GSM8K (math)
- HumanEval (code)
- Perplexity (quant quality)

## license

MIT
