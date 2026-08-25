# LedgerMate

**Offline SME Business Intelligence for Africa**

Africa Deep Tech Challenge 2026 — The Laptop LLM Challenge

## Problem

Small business owners in Cameroon and across Africa keep ledgers on paper, in spreadsheets, or in their heads. When records are lost, damaged, or never reconciled, owners cannot answer basic questions: “How much cash do I have today?”, “Who owes me money?”, “What did I spend last month?”, “Am I profitable?”.

LedgerMate converts natural-language transaction descriptions into structured, validated ledger entries — entirely on-device, with no internet, no cloud fees, and no subscription.

## What it does

- Natural-language transaction entry with mandatory confirmation.
- Deterministic financial calculations using Python Decimal.
- Local AI assistant for business questions, summaries, and insights.
- Dashboard with real KPIs, charts, and business health.
- Invoicing, customers, products, trash/recycle bin, and reports.
- CSV/JSON export; offline PDF-ready report structure.
- 100% offline local inference via llama.cpp + GGUF.

## Example

```
You: I bought fish for 3000 XAF and tomato for 500.

LedgerMate:
- type: expense
- amount: 3,500 XAF
- description: Fish and tomatoes
- category: Food
```

## Why this matters for Africa

- No stable internet required after model download.
- No recurring SaaS costs.
- No data leaves the device.
- Designed for cash, partial payments, and mobile-money-style records — the actual daily reality of African SMEs.

## Architecture

```
Natural language → LLM extraction → Validation layer → Python Decimal engine → SQLite → Dashboard/Reports/AI
```

The LLM interprets intent. The deterministic engine owns arithmetic and ledger integrity.

## Technology

- **Inference:** Llama 3.2 1B Instruct GGUF Q4_K_M via llama.cpp
- **Validation:** Python Decimal deterministic engine
- **Storage:** SQLite with append-only audit log
- **Runtime:** 100% offline, no cloud APIs
- **Target hardware:** 8 GB RAM commodity laptop

## Competition

- **Challenge:** Africa Deep Tech Challenge 2026 — Laptop LLM Track
- **Domain:** Corporate / Enterprise
- **Team:** Solo — Penn Divine Favour
- **Repository:** https://github.com/penndivinefavour-lab/ledgermate

## Quick start

```powershell
# 1. Activate Python 3.12 environment
.\.venv312\Scripts\Activate.ps1

# 2. Verify setup and tests
python verify_setup.py

# 3. Start the offline web dashboard
python run_server.py
# Then open http://127.0.0.1:8000
```

### Launcher behavior
- Uses `run_server.py` as the primary startup path.
- Detects an existing LedgerMate instance on port 8000 and opens it instead of starting a second instance.
- If another unrelated app owns port 8000, prints owner diagnostics and avoids a hard WinError 10048 crash.
- Supports `.\\run_ledgerMate.ps1 -Stop` and `.\\run_ledgerMate.ps1 -Restart`.

> Note: direct `python src\ledgermate\api.py` startup is not the supported path on Windows because the launcher provides the required port guard. Use `python run_server.py` instead.

### Environment variables
- `LEDGERMATE_HOST` — bind host, default `127.0.0.1`
- `LEDGERMATE_PORT` — bind port, default `8000`

## Model license

Llama 3.2 Community License — attribution required: “Built with Llama”.

## LedgerMate code license

MIT License

## Status

LedgerMate — premium offline business intelligence with dashboard, AI assistant, invoicing, customers, products, trash/recycle bin, reports, exports, and verified ADTC 2026 compliance.
