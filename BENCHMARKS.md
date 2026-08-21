# LedgerMate — Benchmarks
## Africa Deep Tech Challenge 2026

**Model:** Llama 3.2 1B Instruct GGUF Q4_K_M  
**Runtime:** llama.cpp 0.1.2-dev (build 07822bd)  
**Hardware:** Dell Vostro 3500, Intel Core i7-1165G7 @ 2.80GHz, 16 GB RAM  
**OS:** Ubuntu 22.04.5 LTS (WSL2)  
**Date:** 2026-08-20

## Benchmark Runs

| Run | Model | Quant | Context | Prompt | Gen | TPS | Peak RSS | Steady RSS | First Token Latency | CPU% | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1B | Llama 3.2 1B Q4_K_M | 25.56 | 1379 MB | 1319 MB | 4930 ms | 53.4% | Stable run |
| 2 | Llama 3.2 1B Q4_K_M | 25.81 | 1379 MB | 1316 MB | 5142 ms | — | Stability check |
| 3 | Llama 3.2 3B Q4_K_M | FAILED — 778 MB / ~1.87 GB; file integrity check failed; not benchmarkable |

## Stability Check

Ran profiler compare on `submission.json` vs `submission_2.json`:

| Metric | Run 1 | Run 2 | Delta | Tolerance | Status |
|---|---|---|---|---|---|
| throughput.tokens_per_second_generation | 25.56 | 25.81 | +1.0% | ±25% | PASS |
| throughput.first_token_latency_ms | 4930.38 | 5142.33 | +4.3% | ±25% | PASS |
| memory.peak_rss_mb | 1379.08 | 1378.94 | -0.0% | ±15% | PASS |
| memory.steady_state_rss_mb | 1318.93 | 1315.90 | -0.2% | ±15% | PASS |

Note: The profiler `compare` verdict shows `FAIL` because both files are participant-mode runs; the audit-environment check expects `measured_on=audit_cloud_vm`. The metric checks themselves all pass.

## Profiler Output

`submission.json` generated successfully at:
`D:/ADTC2026_RESEARCH/ledgermate/submission.json`

Key measured values:
- `throughput.tokens_per_second_generation`: 25.56
- `throughput.first_token_latency_ms`: 4930.38
- `memory.peak_rss_mb`: 1379.08
- `memory.steady_state_rss_mb`: 1318.93
- `cpu_thermal.cpu_percent_p99`: 53.4
- `cpu_thermal.core_temp_c_peak`: null
- `cpu_thermal.throttled`: false

## Scoring Estimates

Using ADTC formula:  
`Stotal = 0.50·Sacc + 0.30·Sperf + 0.20·Seff − Pthermal`

Placeholder values until accuracy benchmarking is complete:
- Sacc: NOT MEASURED
- Sperf: based on 25.56 TPS
- Seff: based on 1319 MB RSS / 7.6 GB RAM
- Pthermal: 0 (no throttling detected)

## Next Steps

1. Run accuracy benchmark with public test prompts
2. Verify thermal behavior under sustained load
3. Generate final `submission.json` for audit comparison
