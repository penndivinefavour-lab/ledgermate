# LedgerMate V2 — Benchmarks
## Date: 2026-08-23
## Model: Llama 3.2 1B Instruct GGUF Q4_K_M
## Tool: llama-bench build 10507 (Windows llama.cpp)

### Prompt processing
- n_prompt: 512
- avg time: 256.80 ms
- stddev: 19.17 ms
- samples: [260.394, 236.092, 273.915] ms

### Generation throughput
- n_gen: 128
- avg TPS: 17.28
- stddev: 0.90 TPS
- samples: [16.2479, 17.7776, 17.8241] TPS

### Notes
- Historical TPS value of 25.47 was from an earlier run with different parameters; the verified current value is 17.28 TPS for 128 generated tokens.
- First-token latency, peak RSS, and steady-state RSS were not captured in this Windows llama-bench output; they remain as historical measured values until a full profiler run is available in WSL.
- These are real measured values, not estimates.
