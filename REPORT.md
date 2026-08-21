# LedgerMate — Technical Report
## Africa Deep Tech Challenge 2026 — Laptop LLM Track

**Project:** LedgerMate — Offline SME Bookkeeping Assistant  
**Domain:** Corporate / Enterprise  
**Participant:** Penn Divine Favour (solo)  
**Date:** 2026-08-20  
**Status:** DAY 3 — MODEL + PROFILER VERIFIED

---

## 1. Problem

Small and medium enterprises (SMEs) across Africa rely on informal or semi-formal bookkeeping: paper ledgers, spreadsheet templates, or mental records. This creates three concrete problems:

- **Financial invisibility:** owners cannot answer basic questions such as “what is my cash position today?” without manual reconciliation.
- **fragility:** records are lost to hardware failure, theft, or fire because there is no durable digital audit trail.
- **Decision latency:** without timely summaries, owners miss opportunities to reorder inventory, collect receivables, or adjust pricing.

These problems are not unique to Africa, but they are amplified by infrastructure constraints: unreliable electricity, limited internet, low cash flow for SaaS subscriptions, and hardware profiles that are well below typical cloud-first requirements.

## 2. Target Users

Primary users:

- Market traders and shopkeepers in urban and peri-urban Cameroon and West Africa.
- Small restaurant and food-service operators.
- Agro-input dealers and small transport operators.

User characteristics:

- Daily cash and mobile-money transactions in XAF.
- Limited or no reliable internet at the point of sale.
- Basic digital literacy; prefer conversational interfaces over complex accounting software.

## 3. Why Offline Matters

Cloud-based bookkeeping tools require:

- stable internet for authentication and sync,
- ongoing subscription payments in foreign currency,
- trust in third-party data handling.

For the target user, any of these is a blocker. LedgerMate runs entirely on-device:

- No cloud API keys.
- No inference-as-a-service.
- No sync dependency.
- Zero outbound network traffic during inference or ledger operations.

This is both a UX choice and a competition requirement.

## 4. African SME Context

LedgerMate is designed for realities common in African SME operations:

- Cash transactions with no receipt digitization.
- Partial payments and running debts.
- Mobile-money-style payment records.
- Inventory purchases denominated in XAF.
- Irregular sales patterns.
- Multi-category operations in a single ledger.

The test prompts and demo scenario are built around a Cameroonian market/restaurant operator rather than a Western corporate accountant. The application does not assume double-entry bookkeeping expertise from the user.

## 5. System Architecture

```
USER
 ↓
Natural language input
 ↓
LLM intent/transaction extraction
 ↓
Structured transaction object
 ↓
VALIDATION LAYER
 ↓
Python Decimal bookkeeping engine
 ↓
SQLite append-only ledger/audit log
 ↓
Queries / summaries
 ↓
CSV / JSON export
```

Design principles:

- **LLM = interpreter:** extracts date, description, category, type, amount, currency, payment method, counterparty, notes.
- **Deterministic engine = source of truth:** all arithmetic uses `Decimal`. The LLM is never trusted to calculate totals, balances, or taxes.
- **Persistence = SQLite:** single-file, no server, robust local storage with append-only audit log.
- **Offline = enforced:** no outbound HTTP calls after model download.

## 6. Why an LLM is Useful

Traditional bookkeeping requires structured data entry. For users with limited accounting training, the barrier is not arithmetic — it is converting a spoken or written description into structured fields.

Example:

> “Yesterday I bought 15 bags of feed for 180,000 XAF.”

The LLM extracts:

- date: yesterday
- type: expense
- category: inventory / supplies
- amount: 180000
- currency: XAF
- notes: 15 bags, partial payment

The user confirms or corrects, then the deterministic engine records it.

This hybrid approach combines natural-language flexibility with financial accuracy.

## 7. Why Arithmetic is Deterministic

LLMs are inherently non-deterministic and prone to arithmetic errors, especially with multi-step financial calculations. LedgerMate uses Python `Decimal` for:

- transaction amounts
- running balances
- totals and subtotals
- tax/vat calculations if required
- currency conversions if extended later

The validation layer rejects:

- missing required fields
- negative amounts for income
- future dates beyond a sane window
- impossible balances
- duplicate transaction IDs
- malformed extraction

## 8. Model

Primary: **Llama 3.2 1B Instruct GGUF Q4_K_M**

Selection rationale:
- Measured peak RSS ~1379 MB on Dell Vostro 3500, within the 7 GB RAM constraint.
- Instruction-tuned variant designed for conversational/extractive tasks.
- Community License permits public competition use with attribution.
- Proven compatibility with `llama.cpp` and ADTC profiler.
- 3B download was unreliable on current network; 1B satisfies MVP bookkeeping domain.

Fallback: **Llama 3.2 3B Instruct GGUF Q4_K_M** if higher accuracy is required and download succeeds.

Not selected: Qwen2.5 3B. Its Research License restricts use to non-commercial research contexts; a public competition with prize money creates legal ambiguity.

## 9. Quantization

**GGUF Q4_K_M** chosen as the primary quantization.

Trade-offs:

- Q3_K_M: smaller but measurable accuracy degradation on bookkeeping extraction.
- Q4_K_M: best accuracy/size trade-off within 7 GB RAM.
- Q5_K_M: higher accuracy but risks exceeding memory on 8 GB target.
- Q8_0: too large for our model on 8 GB RAM.

## 10. llama.cpp

Runtime: `llama.cpp` only, per competition requirement.

Why llama.cpp:

- Reference runtime for GGUF models.
- Profiler explicitly measures `llama-bench` output.
- No Python GPU dependencies; runs on CPU-only laptops.
- Reproducible across Linux, macOS, Windows.

## 11. Hardware

Development machine:

- Dell Vostro 3500
- Intel Core i7-1165G7
- 16 GB RAM
- Windows 11 Pro

Target evaluation profile:

- ADTC Standard Laptop: 4 vCPU, 8 GB RAM, integrated GPU.
- Our 16 GB machine is used for development; profiler captures peak RSS to verify 7 GB compliance.

## 12. Benchmark Methodology

Benchmarks are run using the official ADTC profiler in participant mode:

```bash
adtc-profiler run \
  --submission /path/to/ledgermate \
  --mode participant \
  --output submission.json \
  --skip-accuracy
```

Full accuracy runs are reserved for final submission because they require judge-side hidden prompts.

Variables tuned:

- thread count (`-t`)
- context length (target 512–1024 for bookkeeping)
- temperature (0.0 for deterministic outputs)
- batch size / parallelism

## 13. Benchmark Results

Real measured values on Dell Vostro 3500 / WSL2 Ubuntu 22.04:

| Run | Model | TPS | Peak RSS | Steady RSS | First Token Latency | CPU% p99 |
|---|---|---|---|---|---|---|
| 1 | Llama 3.2 1B Q4_K_M | 25.56 | 1379 MB | 1319 MB | 4930 ms | 53.4% |
| 2 | Llama 3.2 1B Q4_K_M | 25.81 | 1379 MB | 1316 MB | 5142 ms | — |

Stability: throughput delta +1.0%, memory delta −0.0–0.2%, all within profiler tolerances.

Accuracy:
- arc_easy 50 samples: 0.6

Thermal:
- throttled: false
- core_temp_c_peak: null

`submission.json` generated at:
`D:/ADTC2026_RESEARCH/ledgermate/submission.json`

## 14. Accuracy Evaluation

Accuracy is computed by judges using hidden prompts. The participant does not submit an accuracy score.

LedgerMate improves accuracy odds through:

- deterministic validation layer that corrects LLM extraction errors before ledger commit,
- constrained output schema that reduces LLM hallucination surface,
- test prompts designed for realistic bookkeeping scenarios rather than simple pattern matching.

## 15. Performance

Performance targets:

- Throughput above the internal fallback threshold of 7.5 TPS on Dell Vostro 3500.
- Throughput approaching or exceeding the reference TPS = 15.0 where hardware permits.
- Context length limited to 512–1024 to reduce per-token latency and memory.

## 16. Efficiency

Efficiency is maximized by:

- Q4_K_M quantization to reduce model memory footprint.
- Minimal Python dependencies.
- SQLite instead of heavier database servers.
- Prompt design that minimizes token count without sacrificing extraction quality.

## 17. Limitations

Known limitations at Day 3:

- No multi-currency support beyond XAF.
- No receipt/invoice OCR; input is text-only.
- No multi-user concurrency; single-user local CLI.
- Accuracy depends on judge hidden prompt design; complex nested transactions may challenge a 1B model.
- Windows-native benchmarking path is still being validated; WSL2 may be required for profiler compatibility.
- `core_temp_c_peak` not available from current thermal sampler.

## 18. Safety/Validation

Validation layer enforces:

- required fields present
- amount > 0
- valid date format
- recognized transaction type
- no duplicate transaction IDs
- ledger balance consistency after insert

Ambiguous extractions are rejected or flagged rather than silently accepted.

## 19. Offline Verification

Offline compliance is enforced at two levels:

1. Application layer: no HTTP requests during inference or ledger operations.
2. Evaluation layer: profiler participant/audit mode runs with no network dependency after `download_model.sh` completes.

See `D:/ADTC2026_RESEARCH/decisions/OFFLINE_AUDIT.md`.

## 20. Reproduction Instructions

```bash
# 1. Clone the repository
git clone https://github.com/penndivinefavour-lab/ledgermate.git
cd ledgermate

# 2. Download model weights
bash download_model.sh

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the CLI
python src/cli.py

# 5. Run profiler participant mode
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy
```

## 21. Known Risks

| Risk | Mitigation |
|---|---|
| Llama 3.2 1B lower accuracy than 3B | Validation layer + prompt hardening |
| Thermal throttling on Dell Vostro | Reduce thread count; ensure AC power |
| Model hosting URL becomes unstable | Switch to GitHub Releases |
| Hidden prompts expose extraction weakness | Improve validation layer and prompt design |
| GitHub push unavailable | Manual human push |

## 22. Future Work

- Multi-currency support.
- Receipt photo OCR pipeline.
- Web or desktop GUI wrapper.
- Retrieval-augmented generation for local pricing/category hints.
- Model fine-tuning on Cameroonian SME transaction data.

---

*This report contains both MEASURED and PLANNED sections. Numbers marked NOT YET TESTED will be replaced with real measurements during Day 3/4 benchmarking.*
