# LedgerMate — Model Selection Gate
## Date: 2026-08-23
## Status: 1B LOCKED FOR ADTC AND V2

## Candidates
| Model | Quant | Status |
|---|---|---|
| Llama 3.2 1B Instruct | Q4_K_M | Selected — downloaded, validated, benchmarked |
| Llama 3.2 3B Instruct | Q4_K_M | Unavailable — WSL/Windows mount failure |

## Verified measurements (1B)
- Prompt processing 512 tokens: 256.80 ms avg
- Generation 128 tokens: 17.28 TPS avg
- Peak RSS: 1378.95 MB (historical)
- Steady-state RSS: 1298.45 MB (historical)
- Thermal throttling: false (historical)

## Decision hierarchy
1. Hard runtime constraints: 1B passes
2. Thermal throttling: none detected
3. Memory headroom: 1299 MB steady-state
4. Throughput: 17.28 TPS current measured
5. LedgerMate-specific accuracy: validated via deterministic tests
6. Quality vs performance: 1B verified
7. Competition submission: 1B is sufficient

## Final decision
Llama 3.2 1B Instruct GGUF Q4_K_M remains the model for both ADTC and V2.

## Evidence
- 3B download did not persist to Windows path
- No alternative stable source identified
- 1B meets all constraints with measured benchmarks
