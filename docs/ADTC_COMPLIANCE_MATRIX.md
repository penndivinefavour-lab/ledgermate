# LedgerMate V2 — ADTC Compliance Matrix

| Requirement | Source | Implementation | Verification | Status | Risk | Action Required |
|---|---|---|---|---|---|---|
| Public GitHub repo | ADTC template | penndivinefavour-lab/ledgermate | curl HTTP 200 | PASS | Low | None |
| populated metadata.json | ADTC template | metadata.json with team_id, prompts, submitter | JSON valid | PASS | Low | Replace placeholder email |
| Exactly 2 public test prompts | ADTC template | metadata.json test_prompts array | Inspect file | PASS | Low | Supervisor approval |
| download_model.sh | ADTC template | Script with verified 1B URL | bash -n OK | PASS | Low | None |
| REPORT.md | ADTC template | Technical report with measured values | File exists | PASS | Low | None |
| .gitignore excludes model | ADTC template | .gitignore includes model/ and *.gguf | Git status | PASS | Low | None |
| GGUF weights | ADTC template | Llama 3.2 1B Q4_K_M | File 771 MB, hash OK | PASS | Low | None |
| llama.cpp runtime | ADTC template | llama.cpp wrapper in llm.py | Binary available | PASS | Low | None |
| Offline inference | ADTC template | No network calls in runtime | Offline audit PASS | PASS | Low | None |
| 8 GB RAM constraint | ADTC template | 1B peak RSS 1379 MB | Measured | PASS | Low | None |
| Valid profiler submission | ADTC template | submission.json from adtc-profiler | File exists | PASS | Low | None |
| No network during eval | ADTC template | Runtime has no HTTP libs | Code scan | PASS | Low | None |
| License/attribution | ADTC template | LICENSE + MODEL_ATTRIBUTION.md | Files exist | PASS | Low | None |

## V2-specific compliance
| Feature | ADTC Compatible? | Isolation | Notes |
|---|---|---|---|
| Voice input | Not required for ADTC | Isolated in V2 | Not in ADTC build |
| STT providers | Not required for ADTC | Isolated in V2 | Local only if included |
| Agent registry | Not required for ADTC | Isolated in V2 | Development tooling only |
| Mock providers | Not required for ADTC | Isolated in V2 | Test only |
| TUI enhancements | Not required for ADTC | Isolated in V2 | V2 only |

## Competition build strategy
V2 full product includes voice, STT, agents, TUI.
ADTC competition build uses text prompt → llama.cpp → ledger only.
Both share V1 core domain logic.
